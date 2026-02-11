# epm-estudio-titulo — Procesamiento de documentos legales

> Pipeline para extraer, clasificar, limpiar y estandarizar documentos legales
(estudio de títulos, minutas de constitución y minutas de cancelación). Diseñado
para ejecutarse como Azure Functions integradas con servicios de IA y almacenamiento.

## Requisitos

- Python 3.10+
- Azure Functions Core Tools v4+
- Azurite (opcional, para pruebas locales) o una cuenta Azure Storage
- Dependencias del proyecto: `pip install -r requirements.txt`
- Credenciales/configuración en `local.settings.json` (AzureWebJobsStorage,
  OpenAI/Azure OpenAI keys, endpoints)

## Estructura principal

- `function_app.py` — entrada principal para Azure Functions.
- `functions/` — bindings (Blob triggers) y orquestación por documento.
- `processors/` — procesadores por tipo y `base_processor` con pasos reusables.
- `prompts/` — prompts base para clasificación y extracción.
- `schemas/` — esquemas objetivo por grupo (fuente de verdad para Master JSON).
- `services/` — integraciones (Azure OpenAI, Document Intelligence, Cosmos, Datalake).
- `utils/` — utilidades (limpieza JSON, logging).

## Flujo de procesamiento

1. Blob trigger detecta nuevo PDF/archivo en el contenedor.
2. `document_intelligence_service` extrae `raw_text`, `pages[]`, `tables[]` y metadatos.
3. Clasificación: prompt-based (o embeddings en producción) determina `group`.
4. Limpieza: `json_cleaner` normaliza texto (encoding, espacios, fechas).
5. Extracción estructurada: prompt de extracción mapea campos según `schemas/{group}_schema.py`.
6. Validación: validación contra schema, ajustes por transformaciones estándar.
7. Agregación: documentos estandarizados se agregan al `Master JSON` por grupo.
8. Persistencia: guardar `raw` y `standardized` en Data Lake o Cosmos; actualizar índices.

## Uso local y pruebas

1. Activar entorno virtual e instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

2. Ejecutar Azurite (opcional):

```powershell
npm i -g azurite
azurite --silent --location .\azurite --debug .\azurite\debug.log
```

3. Configurar `local.settings.json` con `AzureWebJobsStorage` apuntando a Azurite
   o a tu cuenta Azure Storage.

4. Iniciar Functions host:

```powershell
func start
```

5. Subir archivos de prueba al contenedor que observan los triggers (Storage Explorer,
   Azure CLI o script Python).

## Prompts recomendados

Usa el prompt de clasificación (devuelve `label`, `confidence`, `reasons`, `examples`)
y el prompt de extracción estructurada (devuelve JSON con `value` y `confidence` por campo).
Los prompts deben almacenarse y versionarse en `prompts/`.

## Master JSON

- Archivo: `master_{group}.json`.
- Contiene `metadata` (version, generated_at, document_count), `documents[]` (document_id,
  extracted, provenance, processor_version, confidence) y `stats`.

## Añadir un nuevo grupo

1. Crear `schemas/{nuevo}_schema.py` con los campos esperados.
2. Añadir prompts específicos en `prompts/` si hacen falta.
3. Añadir `processors/{nuevo}_processor.py` heredando de `base_processor`.
4. Registrar reglas/aliases en la configuración central para clasificación.

## Operación y mantenimiento

- Versiona prompts y schemas; registra `processor_version` en cada documento.
- Implementa re-procesado idempotente (marcar documentos procesados).
- Monitoriza métricas: conteos, latencias, fallos por documento.

## Notas

- Para prototipo, prompt-based es más rápido; para escala, migrar a embeddings + KNN/FAISS.
- Guarda copias `raw` antes de cualquier limpieza para auditoría.
- Normaliza fechas y nombres desde el inicio para evitar inconsistencias.

---

Equipo: DATAKNOW S.A.S
