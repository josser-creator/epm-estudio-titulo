# EPM - Estudio de Títulos: Automatización con IA

Este proyecto implementa una solución basada en Azure Functions para automatizar el análisis de documentos legales en el proceso de estudio de títulos para préstamos de vivienda de EPM. Utiliza inteligencia artificial (Azure Document Intelligence y Azure OpenAI) para extraer información estructurada de certificados de tradición y libertad, minutas de constitución y cancelación de hipotecas, y generar los insumos necesarios para que el sistema Conecta elabore borradores de estudios de títulos y minutas.

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Arquitectura](#arquitectura)
- [Estructura del Repositorio](#estructura-del-repositorio)
- [Requisitos Previos](#requisitos-previos)
- [Configuración](#configuración)
- [Despliegue](#despliegue)
- [Uso](#uso)
- [Flujo de Procesamiento](#flujo-de-procesamiento)
- [Orquestación de Casos (Durable Functions)](#orquestación-de-casos-durable-functions)
- [Limpieza Automática de Bronze](#limpieza-automática-de-bronze)
- [Pruebas](#pruebas)
- [Contribución](#contribución)
- [Licencia](#licencia)

---

## Descripción del Proyecto

El área jurídica de EPM requiere mejorar la eficiencia, trazabilidad y calidad del proceso de estudio de títulos para préstamos de vivienda. Actualmente, los documentos se reciben en formatos no estandarizados (fotos en Word, PDFs de baja calidad) y se han detectado riesgos de alteración de certificados.

La solución implementa:

- **Análisis automático de documentos** mediante Azure Document Intelligence (OCR) y Azure OpenAI para extraer campos clave.
- **Tres tipos de documentos procesados**:
  - Estudio de Títulos (`estudio_titulos`)
  - Minuta de Cancelación de Hipoteca (`minuta_cancelacion`)
  - Minuta de Constitución de Hipoteca (`minuta_constitucion`)
- **Almacenamiento en Data Lake** (Bronze, Silver, Gold) y **Cosmos DB** para trazabilidad.
- **Orquestación con Durable Functions** para consolidar todos los documentos de un mismo caso y generar archivos maestros.
- **Limpieza automática** del contenedor Bronze basada en días hábiles.

**Fuera del alcance**:
- Generación de documentos con IA.
- Transformaciones o reglas de negocio aplicadas a la data extraída.
- Integración con sistemas no mencionados (Conecta, Maya).
- Desarrollo de modelos de datos, analíticas o tableros.
- Conexión a fuentes externas.

---

## Arquitectura

![Arquitectura de la solución](docs/arquitectura.png) *(si se desea incluir imagen)*

La solución utiliza los siguientes servicios de Azure:

- **Azure Blob Storage / Data Lake Gen2**: Almacenamiento en capas (Bronze, Silver, Gold).
- **Azure Functions**: Procesamiento basado en eventos (Blob Trigger, Timer Trigger) y orquestación (Durable Functions).
- **Azure Document Intelligence**: Extracción de texto y layout de documentos PDF.
- **Azure OpenAI**: Extracción estructurada de campos mediante prompts especializados.
- **Azure Cosmos DB**: Persistencia de resultados y metadatos para trazabilidad.
- **API Management** (no implementado directamente, pero se menciona en la arquitectura general).

Flujo de datos:
1. El usuario sube un PDF a la carpeta `bronze/conecta/vivienda/1/`.
2. El Blob Trigger detecta el archivo, identifica el tipo de documento por el nombre y lo procesa:
   - OCR con Document Intelligence.
   - Extracción estructurada con OpenAI.
   - Resultado guardado en Silver (`silver/conecta/vivienda/{tipo}/{caso_id}/{process_id}.json`) y Cosmos DB.
3. Un proceso de orquestación (iniciado vía HTTP) consolida todos los archivos de un mismo caso y genera los archivos maestros en Gold (`gold/conecta/vivienda/master/{tipo}/{caso_id}/MASTER-*.json`).
4. Un Timer Trigger mensual elimina archivos antiguos de Bronze según días hábiles de retención.

---

## Estructura del Repositorio

```
.
├── .vscode/                     # Configuración de VS Code para Azure Functions
├── config/
│   ├── __init__.py
│   └── settings.py               # Configuración centralizada con Pydantic
├── functions/
│   ├── __init__.py
│   ├── estudio_titulos_trigger.py
│   ├── minuta_cancelacion_trigger.py
│   └── minuta_constitucion_trigger.py
├── processors/
│   ├── __init__.py
│   ├── base_processor.py          # Procesador base abstracto
│   ├── estudio_titulos_processor.py
│   ├── minuta_cancelacion_processor.py
│   └── minuta_constitucion_processor.py
├── prompts/
│   ├── __init__.py
│   ├── estudio_titulos_prompt.py
│   ├── minuta_cancelacion_prompt.py
│   └── minuta_constitucion_prompt.py
├── schemas/
│   ├── __init__.py
│   ├── base_schema.py
│   ├── estudio_titulos_schema.py
│   ├── minuta_cancelacion_schema.py
│   ├── minuta_constitucion_schema.py
│   └── panel_schemas.py           # Esquemas para el formato PanelFields
├── services/
│   ├── __init__.py
│   ├── base_service.py
│   ├── azure_openai_service.py
│   ├── chunking_service.py
│   ├── cosmos_db_service.py
│   ├── datalake_service.py
│   └── document_intelligence_service.py
├── utils/
│   ├── __init__.py
│   ├── business_days.py           # Cálculo de días hábiles
│   ├── json_cleaner.py            # Limpieza de datos extraídos
│   └── logger.py                   # Configuración de logging
├── tests/
│   └── test_function_app.py       # Pruebas unitarias
├── activities.py                  # Actividades para Durable Functions
├── function_app.py                # Punto de entrada de Azure Functions (Blob, Timer, Durable)
├── local.settings.json            # Configuración local (no versionar)
├── requirements.txt               # Dependencias
├── host.json                      # Configuración del host de Functions
└── README.md                      # Este documento
```

---

## Requisitos Previos

- Una suscripción de Azure con los siguientes recursos creados:
  - **Storage Account (Data Lake Gen2)** con contenedores: `bronze`, `silver`, `gold`.
  - **Document Intelligence** (antiguo Form Recognizer) con modelo prebuilt-layout.
  - **Azure OpenAI** con un despliegue de modelo GPT-4o (o similar).
  - **Cosmos DB** (core SQL) con base de datos y contenedor.
  - **Function App** (Python 3.9+) con las siguientes configuraciones de aplicación.
- Azure Functions Core Tools (para desarrollo local).
- Python 3.9 o superior.
- Extensiones de Azure Functions: `BlobTrigger`, `TimerTrigger`, `DurableFunctions`.

---

## Configuración

1. **Clonar el repositorio**:
   ```bash
   git clone <repo-url>
   cd epm-estudio-titulos
   ```

2. **Crear un entorno virtual** e instalar dependencias:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:
   Copia el archivo `local.settings.json.example` a `local.settings.json` y completa los valores con los de tu suscripción.

   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "<connection-string>",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "DATALAKE_ACCOUNT_NAME": "azsaepmnpdatalakeg2",
       "DATALAKE_ACCOUNT_KEY": "<account-key>",
       "DATALAKE_CONTAINER_BRONZE": "bronze",
       "DATALAKE_CONTAINER_SILVER": "silver",
       "DATALAKE_CONTAINER_GOLD": "gold",
       "DOCUMENT_INTELLIGENCE_ENDPOINT": "https://<resource>.cognitiveservices.azure.com/",
       "DOCUMENT_INTELLIGENCE_KEY": "<key>",
       "DOCUMENT_INTELLIGENCE_MODEL_ID": "prebuilt-layout",
       "AZURE_OPENAI_ENDPOINT": "https://<resource>.openai.azure.com/",
       "AZURE_OPENAI_KEY": "<key>",
       "AZURE_OPENAI_DEPLOYMENT": "gpt-4o",
       "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
       "COSMOS_ENDPOINT": "https://<account>.documents.azure.com:443/",
       "COSMOS_KEY": "<key>",
       "COSMOS_DATABASE_NAME": "estudio_de_titulos",
       "COSMOS_CONTAINER_NAME": "conecta-procesamientos",
       "BRONZE_RETENTION_DAYS": "7",
       "LTV_MAX_THRESHOLD": "0.8",
       "REJECT_IF_ENCUMBRANCES": "true",
       "CONFIDENCE_WEIGHTS": "{\"VIV_PrestamoDireccionMatricula\":0.3,\"VIV_Compradores\":0.2,\"VIV_identificacionCompradores\":0.2,\"GBL_Valordeprestamo\":0.2,\"TPC_ValorComercial\":0.1}"
     }
   }
   ```

   > **Nota**: `CONFIDENCE_WEIGHTS` debe ser un JSON válido como string.

4. **Ejecutar localmente**:
   ```bash
   func start
   ```

---

## Despliegue

### Despliegue en Azure

1. **Crear la Function App** en Azure (Runtime Stack: Python, versión 3.9+).
2. **Configurar las variables de aplicación** en la Function App con los mismos valores que en `local.settings.json`.
3. **Desplegar el código** usando Azure Functions Core Tools, VS Code o GitHub Actions.
   ```bash
   func azure functionapp publish <nombre-function-app>
   ```

### Configuración de Triggers

- **Blob Trigger**: La función `procesar_documento_blob` se activa automáticamente al subir archivos a `bronze/conecta/vivienda/1/`.
- **Timer Trigger**: `cleanup_bronze_timer` se ejecuta el primer día de cada mes (o según la programación configurada).
- **HTTP Starter**: Para iniciar la orquestación, se expone el endpoint `POST /orquestar/sintesis/{caso_id}`.

---

## Uso

### Subir documentos para procesamiento

1. **Preparar los archivos**: Los PDF deben tener nombres que permitan identificar el tipo:
   - Estudio de Títulos: `estudio_de_titulos_<caso>.pdf` (contiene "estudio_de_titulos" o "estudio de titulos").
   - Minuta de Cancelación: `minuta_cancelacion_<caso>.pdf` (contiene "cancelacion").
   - Minuta de Constitución: `minuta_constitucion_<caso>.pdf` (contiene "constitucion").
2. **Subir a Azure Storage**: Colocar el archivo en el contenedor `bronze`, en la ruta `conecta/vivienda/1/`. Puede hacerse con Azure Storage Explorer, AzCopy o SDK.

   Ejemplo: `bronze/conecta/vivienda/1/estudio_de_titulos_caso-123.pdf`

3. **El proceso se ejecutará automáticamente**:
   - El Blob Trigger detecta el archivo, lee el contenido y determina el tipo.
   - Se instancia el procesador correspondiente.
   - El resultado JSON se guarda en `silver/conecta/vivienda/<tipo>/<caso_id>/<process_id>.json` y en Cosmos DB.

### Obtener el resultado

- Desde Cosmos DB: consultar por `procesoId` o `casoId`.
- Desde Data Lake Silver: navegar a la ruta generada.
- El archivo contiene:
  ```json
  {
    "metadata": { ... },
    "datos_extraidos": {
      "PanelFields": [ ... ]
    }
  }
  ```

### Consolidar un caso (orquestación)

Una vez que se hayan procesado todos los documentos de un caso (por ejemplo, estudio de títulos y minutas), se puede iniciar la orquestación para generar los archivos maestros en Gold.

```bash
curl -X POST https://<function-app>.azurewebsites.net/orquestar/sintesis/caso-123
```

La respuesta incluirá URLs para verificar el estado de la orquestación. Al finalizar, se generarán archivos en:
- `gold/conecta/vivienda/master/estudio_titulos/caso-123/MASTER-<uuid>.json`
- `gold/conecta/vivienda/master/minuta_cancelacion/caso-123/MASTER-<uuid>.json`
- `gold/conecta/vivienda/master/minuta_constitucion/caso-123/MASTER-<uuid>.json`

Estos archivos contienen los campos con prefijo `3_` (ej. `3_VIV_PrestamoDireccionMatricula`) y, en el caso de estudio de títulos, metadatos adicionales como confianza y razones de viabilidad.

---

## Flujo de Procesamiento

### 1. Detección de tipo de documento

La función `detectar_tipo_por_nombre` analiza el nombre del archivo y retorna una clave (`EstudioTitulos`, `MinutaCancelacion`, `MinutaConstitucion`) o `None` si no coincide.

### 2. Procesamiento con IA

Cada procesador hereda de `BaseDocumentProcessor` e implementa:
- `system_name`: identificador del sistema.
- `system_prompt`: prompt específico para el tipo de documento (definido en `prompts/`).
- `schema_class`: esquema Pydantic que define la estructura de salida (`PanelFields`).

Pasos:
- **OCR con Document Intelligence**: se obtiene el texto completo y metadatos del PDF.
- **Extracción con OpenAI**: se envía el texto y el prompt; si el texto excede el límite de caracteres, se aplica chunking automático (`ChunkingService`).
- **Limpieza genérica**: `JsonCleaner` elimina espacios redundantes y normaliza.
- **Enriquecimiento con metadatos**: se agrega `_procesamiento` con fecha, origen, etc.
- **Validación específica** (override en cada procesador).

### 3. Persistencia

`persistir_resultados` guarda:
- En **Data Lake Silver**: archivo JSON con metadatos y datos extraídos.
- En **Cosmos DB**: documento con estructura plana para consultas rápidas.

### 4. Orquestación

Las actividades (`activities.py`) se encargan de:
- `leer_resultados_intermedios`: lista y lee todos los JSON de un caso en Silver.
- `sintetizar_resultados`: combina los datos, calcula confianza, evalúa viabilidad (usando reglas configurables) y genera los archivos maestros en Gold.

La viabilidad se evalúa con reglas como:
- Matrícula obligatoria.
- Concepto jurídico favorable/desfavorable.
- Gravámenes vigentes (según configuración).
- Edad del solicitante (si existe) y score crediticio (si existe).

### 5. Limpieza de Bronze

El timer `cleanup_bronze_timer` recorre todos los archivos del contenedor Bronze, calcula los días hábiles transcurridos desde su última modificación hasta la fecha actual, y elimina aquellos que superen el umbral (`BRONZE_RETENTION_DAYS`).

---

## Orquestación de Casos (Durable Functions)

La orquestación se define en `sintetizar_caso_orchestrator`:

1. **Entrada**: `caso_id`.
2. **Actividad 1**: `leer_resultados_intermedios_activity` → obtiene todos los resultados de Silver para ese caso.
3. **Actividad 2**: `generar_resumen_activity` → ejecuta `activity_sintetizar_resultados`, que consolida y guarda en Gold.
4. **Retorno**: rutas de los archivos generados.

Para iniciar la orquestación, se usa el endpoint HTTP `POST /orquestar/sintesis/{caso_id}`. La respuesta incluye un `statusQueryGetUri` para monitorear el progreso.

---

## Limpieza Automática de Bronze

- **Programación**: `0 0 1 * * *` (primer día de cada mes a medianoche UTC).
- **Cálculo de días hábiles**: se utiliza la función `business_days_between` (excluye sábados y domingos) para determinar si un archivo debe ser eliminado.
- **Configuración**: `BRONZE_RETENTION_DAYS` en días hábiles.

---

## Pruebas

Las pruebas unitarias se encuentran en `tests/test_function_app.py`. Para ejecutarlas:

```bash
pytest tests/ -v
```

Se utilizan mocks para simular los servicios de Azure y verificar el comportamiento de las funciones.

---

## Consideraciones Técnicas

- **Calidad de los PDFs**: La extracción depende de la legibilidad de los documentos. PDFs escaneados de baja calidad pueden afectar el OCR.
- **Límites de OpenAI**: Textos muy largos se dividen automáticamente; sin embargo, la precisión puede disminuir en fragmentos.
- **Seguridad**: Las claves de acceso se gestionan mediante variables de entorno. No se deben hardcodear.
- **Monitoreo**: La aplicación utiliza `logging` configurado para enviar trazas a Azure Application Insights (si está habilitado).

---

## Contribución

1. Fork el repositorio.
2. Cree una rama para su feature (`git checkout -b feature/nueva-funcionalidad`).
3. Realice los cambios y agregue pruebas.
4. Asegúrese de que todas las pruebas pasen.
5. Envíe un Pull Request.

---

## Licencia

Este proyecto es propiedad de EPM y su uso está restringido a los términos establecidos en el contrato con DataKnow.

---

**Documentación generada a partir del código fuente y la descripción del proyecto.**