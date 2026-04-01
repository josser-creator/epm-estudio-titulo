import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock
import services.cosmos_db_service as cosmos_mod


def _dummy_settings():
    return SimpleNamespace(
        cosmos_endpoint="https://dummy-cosmos.documents.azure.com:443/",
        cosmos_key="dummy-key",
        cosmos_database_name="conecta-db",
        cosmos_container_name="procesamientos",
    )


def test_initialize_ok(monkeypatch):
    # Settings dummy
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    # CosmosClient -> db -> container
    container = MagicMock()
    container.upsert_item.return_value = {"id": "doc1"}

    db = MagicMock()
    db.create_container_if_not_exists.return_value = container

    client = MagicMock()
    client.create_database_if_not_exists.return_value = db
    client.get_database_account.return_value = {"ok": True}

    # Patch CosmosClient constructor
    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()

    assert svc._client is client
    assert svc._database is db
    assert svc._container is container


def test_initialize_falla_y_lanza(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    def boom(*args, **kwargs):
        raise RuntimeError("init error")

    monkeypatch.setattr(cosmos_mod, "CosmosClient", boom)

    with pytest.raises(RuntimeError, match="init error"):
        cosmos_mod.CosmosDBService()


def test_health_check_true(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    container = MagicMock()
    db = MagicMock(create_container_if_not_exists=MagicMock(return_value=container))
    client = MagicMock(create_database_if_not_exists=MagicMock(return_value=db))
    client.get_database_account.return_value = {"ok": True}

    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()
    assert svc.health_check() is True


def test_health_check_false(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    container = MagicMock()
    db = MagicMock(create_container_if_not_exists=MagicMock(return_value=container))
    client = MagicMock(create_database_if_not_exists=MagicMock(return_value=db))
    client.get_database_account.side_effect = Exception("down")

    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()
    assert svc.health_check() is False


def test_upsert_document_ok_agrega_partition_key(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    container = MagicMock()
    container.upsert_item.return_value = {"id": "doc1"}

    db = MagicMock(create_container_if_not_exists=MagicMock(return_value=container))
    client = MagicMock(create_database_if_not_exists=MagicMock(return_value=db))

    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()

    doc = {"id": "doc1", "x": 1}
    doc_id = svc.upsert_document(doc, partition_key="estudio_titulos")

    assert doc_id == "doc1"
    assert doc["tipoDocumento"] == "estudio_titulos"
    container.upsert_item.assert_called_once()


def test_upsert_document_error_propaga(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    container = MagicMock()
    container.upsert_item.side_effect = RuntimeError("upsert fail")

    db = MagicMock(create_container_if_not_exists=MagicMock(return_value=container))
    client = MagicMock(create_database_if_not_exists=MagicMock(return_value=db))

    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()

    with pytest.raises(RuntimeError, match="upsert fail"):
        svc.upsert_document({"id": "x"}, partition_key="minuta_constitucion")


def test_get_document_ok(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    container = MagicMock()
    container.read_item.return_value = {"id": "doc1", "tipoDocumento": "estudio_titulos"}

    db = MagicMock(create_container_if_not_exists=MagicMock(return_value=container))
    client = MagicMock(create_database_if_not_exists=MagicMock(return_value=db))

    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()
    out = svc.get_document("doc1", "estudio_titulos")

    assert out["id"] == "doc1"
    container.read_item.assert_called_once_with(item="doc1", partition_key="estudio_titulos")


def test_get_document_not_found_retorna_none(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    container = MagicMock()
    # Usa exactamente el tipo que el módulo captura (en tu conftest suele ser KeyError)
    container.read_item.side_effect = cosmos_mod.exceptions.CosmosResourceNotFoundError()

    db = MagicMock(create_container_if_not_exists=MagicMock(return_value=container))
    client = MagicMock(create_database_if_not_exists=MagicMock(return_value=db))

    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()
    assert svc.get_document("missing", "estudio_titulos") is None


def test_get_document_error_propaga(monkeypatch):
    monkeypatch.setattr(cosmos_mod, "get_settings", lambda: _dummy_settings())

    container = MagicMock()
    container.read_item.side_effect = RuntimeError("read fail")

    db = MagicMock(create_container_if_not_exists=MagicMock(return_value=container))
    client = MagicMock(create_database_if_not_exists=MagicMock(return_value=db))

    monkeypatch.setattr(cosmos_mod, "CosmosClient", lambda url, credential: client)

    svc = cosmos_mod.CosmosDBService()

    with pytest.raises(RuntimeError, match="read fail"):
        svc.get_document("doc1", "estudio_titulos")
