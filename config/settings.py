import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuracion centralizada de la aplicacion."""

    # Azure Data Lake Gen2
    datalake_account_name: str = Field(alias="DATALAKE_ACCOUNT_NAME")
    datalake_account_key: str = Field(alias="DATALAKE_ACCOUNT_KEY")
    datalake_container_bronze: str = "bronze"
    datalake_container_silver: str = "silver"
    datalake_container_gold: str = "gold"

    # Azure Document Intelligence
    document_intelligence_endpoint: str = Field(alias="DOCUMENT_INTELLIGENCE_ENDPOINT")
    document_intelligence_key: str = Field(alias="DOCUMENT_INTELLIGENCE_KEY")
    # Modelo personalizado (si se entrena)
    document_intelligence_model_id: str = Field(default="prebuilt-layout", alias="DOCUMENT_INTELLIGENCE_MODEL_ID")

    # Azure OpenAI
    azure_openai_endpoint: str = Field(alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(alias="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", alias="AZURE_OPENAI_API_VERSION")

    # Límites para chunking
    chunk_max_characters: int = Field(default=100000, alias="CHUNK_MAX_CHARACTERS")  # Aprox 25k tokens
    chunk_overlap: int = Field(default=1000, alias="CHUNK_OVERLAP")

    # Azure Cosmos DB
    cosmos_endpoint: str = Field(alias="COSMOS_ENDPOINT")
    cosmos_key: str = Field(alias="COSMOS_KEY")
    cosmos_database_name: str = Field(default="conecta-db", alias="COSMOS_DATABASE_NAME")
    cosmos_container_name: str = Field(default="procesamientos", alias="COSMOS_CONTAINER_NAME")

    # Duración de archivos en bronze (días) para eliminación automática
    bronze_retention_days: int = Field(default=7, alias="BRONZE_RETENTION_DAYS")

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
