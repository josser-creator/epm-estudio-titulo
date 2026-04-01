import pytest
import requests
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.conecta_service import ConectaAPIService


def _dummy_settings():
    return SimpleNamespace(
        conecta_client_id="dummy-id",
        conecta_client_secret="dummy-secret",
        conecta_scope="api://dummy/.default",
        conecta_token_url="https://login.microsoftonline.com/dummy/oauth2/v2.0/token",
        conecta_api_url="https://dummy.apim/conecta/ViviendaRespuestaIA",
    )


def test_initialize_carga_settings(monkeypatch):
    monkeypatch.setattr("services.conecta_service.get_settings", lambda: _dummy_settings())
    service = ConectaAPIService()
    assert service.client_id == "dummy-id"
    assert service.token_url.endswith("/token")
    assert "ViviendaRespuestaIA" in service.api_url


def test_health_check_true_si_token_ok(monkeypatch):
    monkeypatch.setattr("services.conecta_service.get_settings", lambda: _dummy_settings())
    service = ConectaAPIService()
    monkeypatch.setattr(service, "_get_token", lambda: "tok")
    assert service.health_check() is True


def test_health_check_false_si_token_falla(monkeypatch):
    monkeypatch.setattr("services.conecta_service.get_settings", lambda: _dummy_settings())
    service = ConectaAPIService()
    monkeypatch.setattr(service, "_get_token", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert service.health_check() is False


def test_get_token_obtiene_y_cachea(monkeypatch):
    monkeypatch.setattr("services.conecta_service.get_settings", lambda: _dummy_settings())
    service = ConectaAPIService()

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"access_token": "token-1", "expires_in": 3600}

    with patch("services.conecta_service.requests.post", return_value=response) as post:
        t1 = service._get_token()
        assert t1 == "token-1"
        assert service._token == "token-1"
        assert service._token_expires_at is not None
        post.assert_called_once()

        # Segunda llamada debe usar caché (no vuelve a pedir token)
        t2 = service._get_token()
        assert t2 == "token-1"
        post.assert_called_once()  # sigue siendo 1


def test_get_token_propaga_request_exception(monkeypatch):
    monkeypatch.setattr("services.conecta_service.get_settings", lambda: _dummy_settings())
    service = ConectaAPIService()

    with patch("services.conecta_service.requests.post", side_effect=requests.exceptions.RequestException("fail")):
        with pytest.raises(requests.exceptions.RequestException):
            service._get_token()


def test_enviar_resultado_envia_payload_y_headers(monkeypatch):
    monkeypatch.setattr("services.conecta_service.get_settings", lambda: _dummy_settings())
    service = ConectaAPIService()

    monkeypatch.setattr(service, "_get_token", lambda: "tok-123")

    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"ok": True}

    with patch("services.conecta_service.requests.post", return_value=resp) as post:
        out = service.enviar_resultado("caso-1", {"a": 1})
        assert out == {"ok": True}

        args, kwargs = post.call_args
        assert args[0] == service.api_url
        assert kwargs["headers"]["Authorization"] == "Bearer tok-123"
        assert kwargs["json"]["casoId"] == "caso-1"
        assert kwargs["json"]["datosExtraidos"] == {"a": 1}
        assert "timestamp" in kwargs["json"]


def test_enviar_resultado_error_incluye_detalle_response(monkeypatch):
    monkeypatch.setattr("services.conecta_service.get_settings", lambda: _dummy_settings())
    service = ConectaAPIService()
    monkeypatch.setattr(service, "_get_token", lambda: "tok-123")

    err = requests.exceptions.HTTPError("http fail")
    err.response = SimpleNamespace(text="detalle de error")

    with patch("services.conecta_service.requests.post", side_effect=err):
        with pytest.raises(requests.exceptions.HTTPError):
            service.enviar_resultado("caso-1", {"a": 1})
