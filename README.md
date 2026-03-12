```markdown
# EPM Estudio de Título – Legal Document Processing Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Azure Functions](https://img.shields.io/badge/Azure%20Functions-4.x-orange)](https://docs.microsoft.com/azure/azure-functions/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Automated extraction, classification, and structuring of legal documents for property title studies.**  
> This serverless pipeline leverages Azure AI services to transform unstructured PDFs (property certificates, mortgage drafts) into standardized JSON, ready for integration with EPM's Conecta system.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Local Setup](#local-setup)
  - [Configuration](#configuration)
- [Processing Pipeline](#processing-pipeline)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [Local Testing](#local-testing)
  - [Deployment to Azure](#deployment-to-azure)
- [Adding a New Document Type](#adding-a-new-document-type)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The current property title study process at EPM relies on manual review of non‑standardized documents, leading to inefficiencies and risks. This project implements an intelligent document processing pipeline that:

- Automatically detects new PDFs uploaded to Azure Data Lake.
- Extracts text, tables, and metadata using **Azure AI Document Intelligence**.
- Classifies documents (title study, mortgage constitution, mortgage cancellation) using **Azure OpenAI** (GPT-4) with carefully engineered prompts.
- Structures extracted data according to predefined JSON schemas.
- Stores both raw and standardized outputs in **Cosmos DB** and/or **Data Lake**.
- Exposes processed results via a secure **API Management** endpoint for consumption by Conecta.

The solution is designed as a set of **Azure Functions** triggered by blob storage events, ensuring a scalable, cost‑effective, and serverless workflow.

---

## Architecture

![High‑level architecture](docs/architecture-diagram.png)  
*(Placeholder – actual diagram to be added)*

| Component                  | Purpose                                                                      |
|----------------------------|------------------------------------------------------------------------------|
| Azure Data Lake Gen2       | Landing zone for raw PDFs and permanent storage of raw extracted data.       |
| Azure Blob Storage Trigger | Initiates the function execution when a new file arrives.                    |
| Azure Functions            | Orchestrates the entire pipeline: classification, extraction, validation.    |
| Azure AI Document Intelligence | Extracts text, layout, tables, and key-value pairs from documents.       |
| Azure OpenAI Service       | Performs document classification and field‑level extraction using GPT‑4.     |
| Cosmos DB                  | Stores structured Master JSON documents for low‑latency retrieval.           |
| Azure API Management       | Exposes endpoints for Conecta to submit files and retrieve results.          |
| Azure Key Vault            | Securely stores API keys, endpoints, and connection strings.                 |

---

## Prerequisites

- **Python 3.10+** installed.
- **Azure Functions Core Tools** v4+ (for local development).
- **Azurite** (optional, for local storage emulation) or an active Azure Storage account.
- An **Azure subscription** with access to:
  - Azure AI Document Intelligence
  - Azure OpenAI Service (with GPT‑4 or equivalent model deployed)
  - Azure Cosmos DB (NoSQL API)
  - Azure Storage Account (Data Lake Gen2 enabled)
- **Git** for version control.

---

## Getting Started

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/epm-estudio-titulo.git
   cd epm-estudio-titulo
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # On Windows: .\.venv\Scripts\Activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Azure Functions Core Tools** (if not already installed)  
   Follow the [official instructions](https://docs.microsoft.com/azure/azure-functions/functions-run-local).

5. **(Optional) Start Azurite for local storage emulation**
   ```bash
   npm install -g azurite
   azurite --silent --location ./azurite --debug ./azurite/debug.log
   ```

### Configuration

Create a `local.settings.json` file in the project root with the following structure:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",  // or actual connection string
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DOCUMENT_INTELLIGENCE_ENDPOINT": "https://<your-resource>.cognitiveservices.azure.com/",
    "DOCUMENT_INTELLIGENCE_KEY": "<your-key>",
    "AZURE_OPENAI_ENDPOINT": "https://<your-openai-resource>.openai.azure.com/",
    "AZURE_OPENAI_KEY": "<your-key>",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
    "COSMOS_DB_CONNECTION_STRING": "<your-connection-string>",
    "COSMOS_DB_DATABASE_NAME": "TitleStudyDB",
    "COSMOS_DB_CONTAINER_NAME": "ProcessedDocuments",
    "PROCESSED_CONTAINER": "standardized",
    "RAW_CONTAINER": "raw"
  }
}
```

> **Important**: Never commit `local.settings.json` to source control. The repository includes `.gitignore` to prevent accidental commits.

---

## Processing Pipeline

1. **Blob Trigger**  
   A new PDF uploaded to the configured input container (e.g., `landing`) triggers the function.

2. **Text Extraction**  
   `DocumentIntelligenceService` calls Azure AI Document Intelligence to extract:
   - Raw text (`raw_text`)
   - Page‑level content (`pages[]`)
   - Tables (`tables[]`)
   - Document metadata (confidence, OCR details).

3. **Classification**  
   `ClassificationProcessor` uses a prompt‑based call to Azure OpenAI to determine the document type (e.g., `title_study`, `mortgage_constitution`, `mortgage_cancellation`). The response includes a label, confidence score, and reasoning.

4. **Text Cleaning**  
   `JsonCleaner` normalises the extracted text: fixes encoding, normalises whitespace, standardises date formats, and removes extraneous characters.

5. **Structured Extraction**  
   Based on the classification, an extraction prompt is built using the corresponding schema (from `schemas/`). Azure OpenAI returns a JSON object with fields and per‑field confidence.

6. **Validation & Aggregation**  
   - The extracted JSON is validated against the schema (required fields, data types).
   - Multiple documents of the same type are aggregated into a **Master JSON** file (e.g., `master_title_study.json`) containing metadata, a list of processed documents, and summary statistics.

7. **Persistence**  
   - Raw extracted data is saved to the `raw` container in Data Lake.
   - Standardised Master JSON is stored in **Cosmos DB** for fast querying and also optionally in the `standardized` container.
   - An index entry is updated to mark the document as processed (idempotent).

---

## Project Structure

```
epm-estudio-titulo/
├── .vscode/                    # VS Code settings (optional)
├── docs/                        # Architecture diagrams, additional docs
├── function_app.py              # Main Azure Functions entry point
├── functions/
│   ├── __init__.py
│   └── blob_trigger.py          # Blob trigger binding
├── processors/
│   ├── __init__.py
│   ├── base_processor.py        # Base class with reusable steps
│   ├── title_study_processor.py
│   └── mortgage_processor.py
├── prompts/
│   ├── __init__.py
│   ├── classification_prompt.txt
│   ├── title_study_extraction_prompt.txt
│   └── mortgage_extraction_prompt.txt
├── schemas/
│   ├── __init__.py
│   ├── base_schema.py            # Common field definitions
│   ├── title_study_schema.py
│   └── mortgage_schema.py
├── services/
│   ├── __init__.py
│   ├── document_intelligence.py
│   ├── openai_service.py
│   ├── cosmos_service.py
│   └── datalake_service.py
├── utils/
│   ├── __init__.py
│   ├── json_cleaner.py
│   └── logging_config.py
├── tests/                        # Unit and integration tests
├── requirements.txt
├── requirements-dev.txt          # Additional dev dependencies
├── .gitignore
├── local.settings.json.example   # Example configuration (rename and fill)
└── README.md
```

---

## Usage

### Local Testing

1. **Start the Functions host**
   ```bash
   func start
   ```

2. **Upload a test PDF**  
   Use Azure Storage Explorer, Azurite, or a Python script to place a PDF in the container that the trigger watches (e.g., `landing`).

3. **Observe logs**  
   The console will show the pipeline steps: trigger fired, classification result, extraction, and storage confirmation.

4. **Run tests**  
   ```bash
   pytest tests/ -v
   ```

### Deployment to Azure

The project includes infrastructure as code (Bicep/ARM) for reproducible deployments. Follow these steps:

1. **Create Azure resources**  
   Use the provided Bicep template (`infra/main.bicep`) to provision all required services (Storage, Document Intelligence, OpenAI, Cosmos DB, etc.).

2. **Configure CI/CD pipeline**  
   A sample GitHub Actions workflow (`.github/workflows/deploy.yml`) is included. It will:
   - Run tests.
   - Package the function app.
   - Deploy to Azure Functions using the `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` secret.

3. **Set application settings**  
   After deployment, configure the same settings as in `local.settings.json` (but using Azure Key Vault for secrets) in the Function App's Configuration blade.

4. **Verify deployment**  
   Upload a document to the input container and monitor Application Insights for successful execution.

---

## Adding a New Document Type

To extend the pipeline for a new document type (e.g., `property_registration`):

1. **Create a schema**  
   In `schemas/`, create a file `new_type_schema.py` defining the expected JSON fields (including any nested structures).

2. **Write extraction prompt**  
   Add a new prompt file in `prompts/`, e.g., `new_type_extraction_prompt.txt`, instructing the model to output JSON matching the schema.

3. **Implement processor**  
   Create `processors/new_type_processor.py` inheriting from `BaseProcessor`. Override methods if special handling is needed (e.g., custom validation).

4. **Update classification prompt**  
   Modify `prompts/classification_prompt.txt` to include the new document type and examples.

5. **Register the processor**  
   In the main orchestrator (`function_app.py` or a factory), map the classifier label to the new processor class.

---

## Monitoring & Maintenance

- **Logging**: All steps are logged with appropriate severity. Use Azure Application Insights to query logs and set up alerts.
- **Idempotency**: Processed documents are flagged in Cosmos DB to avoid reprocessing. The blob trigger uses `BlobClient` with lease management to prevent concurrent processing.
- **Versioning**: Both prompts and schemas are versioned. The `processor_version` field in the Master JSON records the version of code/schema used.
- **Cost optimisation**: Monitor Azure OpenAI token usage and Document Intelligence page counts. Consider caching classification results for identical documents.
- **Fallback & manual review**: If classification confidence is below a threshold (e.g., 0.7), the document is moved to a `needs_review` container and a notification is sent.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

Ensure that your code passes all tests and includes appropriate documentation.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Team:** DATAKNOW S.A.S  
**Contact:** [your-email@dataknow.com](mailto:your-email@dataknow.com)
```