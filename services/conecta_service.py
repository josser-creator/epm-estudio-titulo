import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from .base_service import BaseService
from config import get_settings

class ConectaAPIService(BaseService):
    """Servicio para enviar datos a la API de Conecta."""
    
    def __init__(self):
        super().__init__()
        self._settings = get_settings()
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self.initialize()
    
    def initialize(self) -> None:
        """Inicializa el cliente de la API."""
        self._log_info("Conecta API Service inicializado")
        # Los settings deben tener estas variables de entorno
        self.client_id = self._settings.conecta_client_id
        self.client_secret = self._settings.conecta_client_secret
        self.scope = self._settings.conecta_scope
        self.token_url = self._settings.conecta_token_url
        self.api_url = self._settings.conecta_api_url
    
    def health_check(self) -> bool:
        """Verifica si podemos obtener un token."""
        try:
            self._get_token()
            return True
        except Exception:
            return False
    
    def _get_token(self) -> str:
        """
        Obtiene un token de acceso de Azure AD.
        Implementa caché simple para evitar pedir token en cada llamada.
        """
        # Verificar si el token actual aún es válido (con 5 minutos de margen)
        if self._token and self._token_expires_at:
            now = datetime.utcnow()
            if now < self._token_expires_at:
                self._log_info("Usando token existente")
                return self._token
        
        self._log_info("Obteniendo nuevo token de Azure AD")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self._token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            
            # Calcular expiración (restando 5 minutos para margen)
            self._token_expires_at = datetime.utcnow() + datetime.timedelta(seconds=expires_in - 300)
            
            self._log_info(f"Token obtenido exitosamente, válido por {expires_in} segundos")
            return self._token
            
        except requests.exceptions.RequestException as e:
            self._log_error("Error obteniendo token de Azure AD", error=e)
            raise
    
    def enviar_resultado(self, caso_id: str, datos_extraidos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía los resultados del procesamiento a la API de Conecta.
        
        Args:
            caso_id: ID del caso (generalmente el nombre del archivo sin extensión)
            datos_extraidos: Datos estructurados extraídos del documento
        
        Returns:
            Respuesta de la API de Conecta
        """
        self._log_info(f"Enviando resultado a Conecta para caso {caso_id}")
        
        # Obtener token
        token = self._get_token()
        
        # Preparar headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Construir el payload según lo que espere Conecta
        # Según la documentación, la API espera algo como:
        # {
        #   "casoId": "...",
        #   "datosExtraidos": {...}
        # }
        payload = {
            "casoId": caso_id,
            "datosExtraidos": datos_extraidos,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            self._log_info(f"Respuesta exitosa de Conecta: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            self._log_error(f"Error enviando a Conecta", error=e)
            # Capturar detalles de la respuesta si está disponible
            if hasattr(e, 'response') and e.response:
                self._log_error(f"Detalles de respuesta: {e.response.text}")
            raise

