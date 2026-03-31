# import os
# from functools import lru_cache
# from pydantic import Field, ConfigDict
# from pydantic_settings import BaseSettings


# class Settings(BaseSettings):
#     """Configuración centralizada de la aplicación."""

#     model_config = ConfigDict(
#         env_file=".env", #.env.test para pruebas
#         case_sensitive=False
#     )

#     # Azure Data Lake Gen2
#     datalake_account_name: str = Field(alias="DATALAKE_ACCOUNT_NAME")
#     datalake_account_key: str = Field(alias="DATALAKE_ACCOUNT_KEY")
#     datalake_container_bronze: str = "bronze"
#     datalake_container_silver: str = "silver"
#     datalake_container_gold: str = "gold"

#     # Azure Document Intelligence
#     document_intelligence_endpoint: str = Field(alias="DOCUMENT_INTELLIGENCE_ENDPOINT")
#     document_intelligence_key: str = Field(alias="DOCUMENT_INTELLIGENCE_KEY")
#     document_intelligence_model_id: str = Field(
#         default="prebuilt-layout",
#         alias="DOCUMENT_INTELLIGENCE_MODEL_ID"
#     )

#     # Azure OpenAI
#     azure_openai_endpoint: str = Field(alias="AZURE_OPENAI_ENDPOINT")
#     azure_openai_key: str = Field(alias="AZURE_OPENAI_KEY")
#     azure_openai_deployment: str = Field(
#         default="gpt-4o",
#         alias="AZURE_OPENAI_DEPLOYMENT"
#     )
#     azure_openai_api_version: str = Field(
#         default="2024-02-15-preview",
#         alias="AZURE_OPENAI_API_VERSION"
#     )

#     # Límites para chunking
#     chunk_max_characters: int = Field(
#         default=100000,
#         alias="CHUNK_MAX_CHARACTERS"
#     )
#     chunk_overlap: int = Field(
#         default=1000,
#         alias="CHUNK_OVERLAP"
#     )

#     # Azure Cosmos DB
#     cosmos_endpoint: str = Field(alias="COSMOS_ENDPOINT")
#     cosmos_key: str = Field(alias="COSMOS_KEY")
#     cosmos_database_name: str = Field(
#         default="conecta-db",
#         alias="COSMOS_DATABASE_NAME"
#     )
#     cosmos_container_name: str = Field(
#         default="procesamientos",
#         alias="COSMOS_CONTAINER_NAME"
#     )

#     # Duración de archivos en bronze (días) para eliminación automática
#     bronze_retention_days: int = Field(
#         default=7,
#         alias="BRONZE_RETENTION_DAYS"
#     )

#     # --- Reglas de viabilidad y confianza ---

#     # Umbral máximo de Loan-to-Value (LTV)
#     ltv_max_threshold: float = Field(
#         default=0.8,
#         alias="LTV_MAX_THRESHOLD"
#     )

#     # Rechazar automáticamente si hay gravámenes
#     reject_if_encumbrances: bool = Field(
#         default=True,
#         alias="REJECT_IF_ENCUMBRANCES"
#     )

#     # Pesos para cálculo de confianza
#     confidence_weights: dict = Field(
#         default={
#             "VIV_PrestamoDireccionMatricula": 0.3,
#             "VIV_Compradores": 0.2,
#             "VIV_identificacionCompradores": 0.2,
#             "GBL_Valordeprestamo": 0.2,
#             "TPC_ValorComercial": 0.1,
#         },
#         alias="CONFIDENCE_WEIGHTS"
#     )


# @lru_cache()
# def get_settings() -> Settings:
#     return Settings()

import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Permite elegir el archivo de entorno sin tocar código:
# - Prod: no seteas nada -> usa ".env"
# - Test: SETTINGS_ENV_FILE=".env.test"
_ENV_FILE_RAW = os.getenv("SETTINGS_ENV_FILE", ".env").strip()
_ENV_FILE = None if _ENV_FILE_RAW.lower() in {"", "none", "null", "0"} else _ENV_FILE_RAW


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # <- CLAVE: evita que `conecta_*` rompa la app/tests
    )

    # Azure Data Lake Gen2
    datalake_account_name: str = Field(alias="DATALAKE_ACCOUNT_NAME")
    datalake_account_key: str = Field(alias="DATALAKE_ACCOUNT_KEY")
    datalake_container_bronze: str = "bronze"
    datalake_container_silver: str = "silver"
    datalake_container_gold: str = "gold"

    # Azure Document Intelligence
    document_intelligence_endpoint: str = Field(alias="DOCUMENT_INTELLIGENCE_ENDPOINT")
    document_intelligence_key: str = Field(alias="DOCUMENT_INTELLIGENCE_KEY")
    document_intelligence_model_id: str = Field(
        default="prebuilt-layout",
        alias="DOCUMENT_INTELLIGENCE_MODEL_ID",
    )

    # Azure OpenAI
    azure_openai_endpoint: str = Field(alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(alias="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", alias="AZURE_OPENAI_API_VERSION")

    # Límites para chunking
    chunk_max_characters: int = Field(default=100000, alias="CHUNK_MAX_CHARACTERS")
    chunk_overlap: int = Field(default=1000, alias="CHUNK_OVERLAP")

    # Azure Cosmos DB
    cosmos_endpoint: str = Field(alias="COSMOS_ENDPOINT")
    cosmos_key: str = Field(alias="COSMOS_KEY")
    cosmos_database_name: str = Field(default="conecta-db", alias="COSMOS_DATABASE_NAME")
    cosmos_container_name: str = Field(default="procesamientos", alias="COSMOS_CONTAINER_NAME")

    # Duración de archivos en bronze (días)
    bronze_retention_days: int = Field(default=7, alias="BRONZE_RETENTION_DAYS")

    # --- Reglas de viabilidad y confianza ---
    ltv_max_threshold: float = Field(default=0.8, alias="LTV_MAX_THRESHOLD")
    reject_if_encumbrances: bool = Field(default=True, alias="REJECT_IF_ENCUMBRANCES")

    # Umbral máximo de Loan-to-Value (LTV)
    ltv_max_threshold: float = Field(
        default=0.8,
        alias="LTV_MAX_THRESHOLD"
    )

    # Rechazar automáticamente si hay gravámenes
    reject_if_encumbrances: bool = Field(
        default=True,
        alias="REJECT_IF_ENCUMBRANCES"
    )

    # Conecta API
    conecta_client_id: str = Field(alias="CONECTA_CLIENT_ID")
    conecta_client_secret: str = Field(alias="CONECTA_CLIENT_SECRET")
    conecta_scope: str = Field(
        default="api://135bd0e9-a231-4869-9e15-23c2c3becb15/.default",
        alias="CONECTA_SCOPE" 
    )
    conecta_token_url: str = Field(
        default="https://login.microsoftonline.com/bf1ce8b5-5d39-4bc5-ad6e-07b3e4d7d67a/oauth2/v2.0/token",
        alias="CONECTA_TOKEN_URL"
    )
    conecta_api_url: str = Field(
        default="https://apimnp.epm.com.co/Conecta/ViviendaRespuestaIA",
        alias="CONECTA_API_URL"
    )

    # Pesos para cálculo de confianza 
    confidence_weights: dict = Field(
        default={
            "VIV_PrestamoDireccionMatricula": 0.3,
            "VIV_Compradores": 0.2,
            "VIV_identificacionCompradores": 0.2,
            "GBL_Valordeprestamo": 0.2,
            "TPC_ValorComercial": 0.1,
        },
        alias="CONFIDENCE_WEIGHTS",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


