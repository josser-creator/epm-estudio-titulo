import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuracion centralizada de la aplicacion."""

    # Azure Data Lake Gen2
    datalake_account_name: str = Field(default="", alias="DATALAKE_ACCOUNT_NAME")
    datalake_account_key: str = Field(default="", alias="DATALAKE_ACCOUNT_KEY")
    datalake_container_bronze: str = Field(default="bronze", alias="DATALAKE_CONTAINER_BRONZE")
    datalake_container_silver: str = Field(default="silver", alias="DATALAKE_CONTAINER_SILVER")

    # Azure Document Intelligence
    document_intelligence_endpoint: str = Field(default="", alias="DOCUMENT_INTELLIGENCE_ENDPOINT")
    document_intelligence_key: str = Field(default="", alias="DOCUMENT_INTELLIGENCE_KEY")

    # Azure OpenAI
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(default="", alias="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", alias="AZURE_OPENAI_API_VERSION")

    # Rutas de sistemas
    path_estudio_titulos: str = "bronze/conecta/vivienda/estudio_de_titulos"
    path_minuta_cancelacion: str = "bronze/conecta/vivienda/minuta_de_cancelacion"
    path_minuta_constitucion: str = "bronze/conecta/vivienda/minuta_de_constitucion"

    # Azure Cosmos DB
    cosmos_endpoint: str = Field(default="", alias="COSMOS_ENDPOINT")
    cosmos_key: str = Field(default="", alias="COSMOS_KEY")
    cosmos_database_name: str = Field(default="conecta-db", alias="COSMOS_DATABASE_NAME")
    cosmos_container_name: str = Field(default="procesamientos", alias="COSMOS_CONTAINER_NAME")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Retorna instancia cacheada de Settings."""
    return Settings()
