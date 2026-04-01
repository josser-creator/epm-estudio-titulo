"""
Pruebas unitarias para services/core.py. Se enfocan en la lógica de negocio de los servicios, no en la integración con Azure o 
el formato exacto de los datos.
Se usan mocks para simular las dependencias externas (como los clientes de Azure) y para controlar el comportamiento de las funciones internas.
Las pruebas verifican que los servicios manejen correctamente las operaciones de lectura, escritura, listado y eliminación de archivos en el datalake, 
que procesen los resultados de Document Intelligence adecuadamente, y que realicen las operaciones de Cosmos DB según lo esperado.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from services.datalake_service import DataLakeService
from services.document_intelligence_service import DocumentIntelligenceService
from services.cosmos_db_service import CosmosDBService


@patch("services.datalake_service.DataLakeServiceClient")
def test_datalake_read_write_list_delete(mock_client_cls):
    # client -> file_system_client -> file_client
    download = MagicMock()
    download.readall.return_value = b"hello"

    file_client = MagicMock()
    file_client.download_file.return_value = download

    dir_client = MagicMock()
    fs_client = MagicMock()
    fs_client.get_file_client.return_value = file_client
    fs_client.get_directory_client.return_value = dir_client

    client = MagicMock()
    client.get_file_system_client.return_value = fs_client
    mock_client_cls.return_value = client

    svc = DataLakeService()
    assert svc.health_check() is True

    assert svc.read_file("silver", "a.txt") == b"hello"
    out_path = svc.write_json("silver", "dir/a.json", {"x": 1})
    assert out_path == "silver/dir/a.json"

    # list_files
    fs_client.get_paths.return_value = [
        SimpleNamespace(is_directory=False, name="dir/a.json"),
        SimpleNamespace(is_directory=False, name="dir/b.pdf"),
        SimpleNamespace(is_directory=True, name="dir/sub"),
    ]
    files = svc.list_files("silver", "dir", extension=".json")
    assert files == ["dir/a.json"]

    assert svc.delete_file("silver", "dir/a.json") is True
    file_client.delete_file.assert_called()


def test_document_intelligence_process_result_cubre_pages_tables_paragraphs():
    svc = DocumentIntelligenceService()

    fake_result = SimpleNamespace(
        content="texto",
        pages=[
            SimpleNamespace(
                page_number=1,
                width=100,
                height=200,
                lines=[
                    SimpleNamespace(
                        content="línea 1",
                        polygon=[SimpleNamespace(x=0, y=0), SimpleNamespace(x=1, y=1)],
                    )
                ],
            )
        ],
        tables=[
            SimpleNamespace(
                row_count=1,
                column_count=1,
                cells=[SimpleNamespace(row_index=0, column_index=0, content="c", kind="columnHeader")],
            )
        ],
        paragraphs=[SimpleNamespace(content="p", role="title")],
    )

    data = svc._process_analysis_result(fake_result)
    assert data["content"] == "texto"
    assert data["pages"][0]["lines"][0]["content"] == "línea 1"
    assert data["tables"][0]["cells"][0]["is_header"] is True
    assert data["paragraphs"][0]["role"] == "title"


def test_cosmos_upsert_y_get_document(monkeypatch):
    svc = CosmosDBService()

    # upsert
    doc = {"id": "1"}
    doc_id = svc.upsert_document(doc, partition_key="estudio_titulos")
    assert doc_id == "1"

    # get ok
    got = svc.get_document("1", "estudio_titulos")
    assert got["id"] == "1"

    # get not found
    svc._container.read_item = MagicMock(side_effect=KeyError())
    assert svc.get_document("2", "estudio_titulos") is None