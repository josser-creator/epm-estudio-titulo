#!/usr/bin/env python
"""
Script para probar la conexión a la API de Conecta.
Ejecutar: python test_conecta_api.py
"""

import sys
import os
import json

# Agregar la ruta del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.conecta_service import ConectaAPIService
from config import get_settings

def test_conecta_api():
    print("=" * 50)
    print("Probando conexión a API de Conecta")
    print("=" * 50)
    
    # Verificar configuración
    settings = get_settings()
    
    print(f"API URL: {settings.conecta_api_url}")
    print(f"Token URL: {settings.conecta_token_url}")
    print(f"Client ID: {settings.conecta_client_id}")
    print(f"Scope: {settings.conecta_scope}")
    
    # Inicializar servicio
    print("\n1. Inicializando servicio...")
    service = ConectaAPIService()
    
    # Health check
    print("\n2. Realizando health check...")
    if service.health_check():
        print("✓ Health check exitoso")
    else:
        print("✗ Health check falló")
        return
    
    # Datos de prueba
    datos_prueba = {
        "PanelFields": [
            {"InternalName": "VIV_PrestamoDireccionMatricula", "Type": "Text", "TextValue": "050C-12345678"},
            {"InternalName": "VIV_Compradores", "Type": "Text", "TextValue": "PRUEBA TEST"},
            {"InternalName": "GBL_Valordeprestamo", "Type": "Number", "NumberValue": 100000000}
        ],
        "_test": True,
        "_timestamp": "2025-03-20T10:00:00"
    }
    
    # Enviar datos de prueba
    print("\n3. Enviando datos de prueba a Conecta...")
    try:
        response = service.enviar_resultado(
            caso_id="TEST_CASE_001",
            datos_extraidos=datos_prueba
        )
        print("✓ Envío exitoso!")
        print(f"Respuesta: {json.dumps(response, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    print("\n" + "=" * 50)
    print("Prueba completada")
    print("=" * 50)

if __name__ == "__main__":
    test_conecta_api()