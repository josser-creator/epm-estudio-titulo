import json
from typing import Optional
from azure.storage.filedatalake import DataLakeServiceClient

from .base_service import BaseService
from config import get_settings


class DataLakeService(BaseService):
    """Servicio para interactuar con Azure Data Lake Gen2."""

    def __init__(self):
        super().__init__()
        self._client: Optional[DataLakeServiceClient] = None
        self._settings = get_settings()
        self.initialize()

    def initialize(self) -> None:
        """Inicializa el cliente de Data Lake."""
        try:
            account_url = f"https://{self._settings.datalake_account_name}.dfs.core.windows.net"
            self._client = DataLakeServiceClient(
                account_url=account_url,
                credential=self._settings.datalake_account_key
            )
            self._log_info("Data Lake client initialized successfully")
        except Exception as e:
            self._log_error("Failed to initialize Data Lake client", error=e)
            raise

    def health_check(self) -> bool:
        """Verifica que el servicio este disponible."""
        return self._client is not None

    def read_file(self, container: str, file_path: str) -> bytes:
        """
        Lee un archivo del Data Lake.

        Args:
            container: Nombre del contenedor (filesystem).
            file_path: Ruta del archivo dentro del contenedor.

        Returns:
            bytes: Contenido del archivo.
        """
        try:
            self._log_info(f"Reading file from {container}/{file_path}")

            file_system_client = self._client.get_file_system_client(container)
            file_client = file_system_client.get_file_client(file_path)

            download = file_client.download_file()
            content = download.readall()

            self._log_info(f"File read successfully, size: {len(content)} bytes")
            return content

        except Exception as e:
            self._log_error(f"Failed to read file {container}/{file_path}", error=e)
            raise

    def write_json(self, container: str, file_path: str, data: dict) -> str:
        """
        Escribe un archivo JSON al Data Lake.

        Args:
            container: Nombre del contenedor (filesystem).
            file_path: Ruta del archivo dentro del contenedor.
            data: Diccionario a guardar como JSON.

        Returns:
            str: Ruta completa del archivo guardado.
        """
        try:
            self._log_info(f"Writing JSON to {container}/{file_path}")

            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            content_bytes = json_content.encode('utf-8')

            file_system_client = self._client.get_file_system_client(container)

            # Crear directorios si no existen
            directory_path = "/".join(file_path.split("/")[:-1])
            if directory_path:
                directory_client = file_system_client.get_directory_client(directory_path)
                try:
                    directory_client.create_directory()
                except Exception:
                    pass  # El directorio ya existe

            file_client = file_system_client.get_file_client(file_path)
            file_client.upload_data(content_bytes, overwrite=True)

            full_path = f"{container}/{file_path}"
            self._log_info(f"JSON written successfully to {full_path}")
            return full_path

        except Exception as e:
            self._log_error(f"Failed to write JSON to {container}/{file_path}", error=e)
            raise

    def file_exists(self, container: str, file_path: str) -> bool:
        """
        Verifica si un archivo existe en el Data Lake.

        Args:
            container: Nombre del contenedor (filesystem).
            file_path: Ruta del archivo dentro del contenedor.

        Returns:
            bool: True si el archivo existe, False en caso contrario.
        """
        try:
            file_system_client = self._client.get_file_system_client(container)
            file_client = file_system_client.get_file_client(file_path)
            file_client.get_file_properties()
            return True
        except Exception:
            return False

    def list_files(self, container: str, directory_path: str, extension: str = None) -> list:
        """
        Lista archivos en un directorio del Data Lake.

        Args:
            container: Nombre del contenedor (filesystem).
            directory_path: Ruta del directorio.
            extension: Extension de archivo a filtrar (ej: ".pdf").

        Returns:
            list: Lista de rutas de archivos.
        """
        try:
            file_system_client = self._client.get_file_system_client(container)
            paths = file_system_client.get_paths(path=directory_path)

            files = []
            for path in paths:
                if not path.is_directory:
                    if extension is None or path.name.lower().endswith(extension.lower()):
                        files.append(path.name)

            self._log_info(f"Found {len(files)} files in {container}/{directory_path}")
            return files

        except Exception as e:
            self._log_error(f"Failed to list files in {container}/{directory_path}", error=e)
            raise

    def delete_file(self, container: str, file_path: str) -> bool:
        """
        Elimina un archivo del Data Lake.

        Args:
            container: Nombre del contenedor (filesystem).
            file_path: Ruta del archivo dentro del contenedor.

        Returns:
            bool: True si se elimino correctamente.
        """
        try:
            file_system_client = self._client.get_file_system_client(container)
            file_client = file_system_client.get_file_client(file_path)
            file_client.delete_file()

            self._log_info(f"File deleted: {container}/{file_path}")
            return True

        except Exception as e:
            self._log_error(f"Failed to delete file {container}/{file_path}", error=e)
            raise
