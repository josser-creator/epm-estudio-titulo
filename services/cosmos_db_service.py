import logging
from typing import Optional, Dict, Any
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from .base_service import BaseService
from config import get_settings

class CosmosDBService(BaseService):
    """Servicio para interactuar con Azure Cosmos DB."""

    def __init__(self):
        super().__init__()
        self._client: Optional[CosmosClient] = None
        self._database = None
        self._container = None
        self._settings = get_settings()
        self.initialize()

    def initialize(self) -> None:
        """Inicializa el cliente de Cosmos DB y asegura base de datos y contenedor."""
        try:
            self._client = CosmosClient(
                url=self._settings.cosmos_endpoint,
                credential=self._settings.cosmos_key
            )
            # Crear base de datos si no existe
            self._database = self._client.create_database_if_not_exists(
                id=self._settings.cosmos_database_name
            )
            # Crear contenedor con partition key /tipo_documento o /caso_id
            self._container = self._database.create_container_if_not_exists(
                id=self._settings.cosmos_container_name,
                partition_key=PartitionKey(path="/tipoDocumento"),
                offer_throughput=400
            )
            self._log_info("Cosmos DB client initialized successfully")
        except Exception as e:
            self._log_error("Failed to initialize Cosmos DB client", error=e)
            raise

    def health_check(self) -> bool:
        """Verifica conectividad con Cosmos DB."""
        try:
            self._client.get_database_account()
            return True
        except Exception:
            return False

    def upsert_document(self, document: Dict[str, Any], partition_key: str) -> str:
        """
        Inserta o reemplaza un documento en el contenedor.

        Args:
            document: Documento a guardar (debe incluir un campo 'id' único).
            partition_key: Valor de la clave de partición.

        Returns:
            str: ID del documento insertado.
        """
        try:
            # Agregar campo de partición si no está en el documento
            document["tipoDocumento"] = partition_key
            result = self._container.upsert_item(body=document)
            self._log_info(f"Document upserted with id: {result['id']}")
            return result["id"]
        except Exception as e:
            self._log_error("Failed to upsert document in Cosmos DB", error=e)
            raise

    def get_document(self, doc_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """Recupera un documento por id y clave de partición."""
        try:
            item = self._container.read_item(item=doc_id, partition_key=partition_key)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            self._log_error("Failed to read document from Cosmos DB", error=e)
            raise