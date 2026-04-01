"""
Pruebas unitarias para activities.py. Se enfocan en la lógica de negocio, no en la integración con Azure o el formato exacto de los datos.
Se usan mocks para simular la lectura y escritura en el datalake, y para controlar los settings. 
Las pruebas verifican que las funciones procesen los datos correctamente, apliquen las reglas de negocio 
(como el cálculo de confianza y la evaluación de viabilidad) y generen las salidas esperadas.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import activities


def test_panel_fields_to_dict_y_add_prefix():
    panel = [
        {"InternalName": "A", "Type": "Text", "TextValue": "x"},
        {"InternalName": "B", "Type": "Number", "NumberValue": 10},
    ]
    d = activities.panel_fields_to_dict(panel)
    assert d == {"A": "x", "B": 10}

    pref = activities.add_prefix_to_panel_fields(panel, prefix="3_")
    assert pref[0]["InternalName"] == "3_A"
    assert pref[1]["InternalName"] == "3_B"


def test_calcular_confianza_usa_pesos_y_presencia_campos(monkeypatch):
    fake_settings = SimpleNamespace(
        confidence_weights={
            "VIV_PrestamoDireccionMatricula": 0.6,
            "VIV_Compradores": 0.4,
        }
    )
    monkeypatch.setattr(activities, "settings", fake_settings)

    resultados = [
        {"datos": {"PanelFields": [
            {"InternalName": "VIV_PrestamoDireccionMatricula", "Type": "Text", "TextValue": "050C-1"},
            {"InternalName": "VIV_Compradores", "Type": "Text", "TextValue": ""},
        ]}},
    ]

    # aciertos = 0.6, total = 1.0
    assert activities.calcular_confianza(resultados) == 0.6


def test_evaluar_viabilidad_rechaza_sin_matricula(monkeypatch):
    fake_settings = SimpleNamespace(reject_if_encumbrances=True)
    monkeypatch.setattr(activities, "settings", fake_settings)

    field_dicts = {"estudio_titulos": {"VIV_PrestamoDireccionMatricula": ""}}
    out = activities.evaluar_viabilidad([], field_dicts)

    assert out["status"] == "REJECTED"
    assert any(r["code"] == "MISSING_MATRICULA" for r in out["reasons"])


def test_evaluar_viabilidad_rechaza_embargo_vigente(monkeypatch):
    fake_settings = SimpleNamespace(reject_if_encumbrances=True)
    monkeypatch.setattr(activities, "settings", fake_settings)

    field_dicts = {"estudio_titulos": {
        "VIV_PrestamoDireccionMatricula": "050C-1",
        "VIV_gravamenes": "Embargo vigente sobre el inmueble",
    }}
    out = activities.evaluar_viabilidad([], field_dicts)

    assert out["status"] == "REJECTED"
    assert any(r["code"] == "EMBARGO_VIGENTE" for r in out["reasons"])


def test_activity_leer_resultados_intermedios_lee_y_normaliza(monkeypatch):
    fake_datalake = MagicMock()
    fake_settings = SimpleNamespace(datalake_container_silver="silver")

    # simula que para estudio-titulos hay 1 json, para los otros nada
    fake_datalake.list_files.side_effect = [
        ["conecta/vivienda/estudio-titulos/caso-1/p1.json"],
        [],
        [],
    ]
    payload = {
        "metadata": {"proceso_id": "p1", "caso_id": "caso-1"},
        "datos_extraidos": {"PanelFields": [{"InternalName": "X", "Type": "Text", "TextValue": "y"}]},
    }
    fake_datalake.read_file.return_value = json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(activities, "datalake", fake_datalake)
    monkeypatch.setattr(activities, "settings", fake_settings)

    out = activities.activity_leer_resultados_intermedios("caso-1")
    assert out[0]["tipo"] == "estudio_titulos"
    assert out[0]["process_id"] == "p1"
    assert out[0]["caso_id"] == "caso-1"


def test_activity_sintetizar_resultados_genera_master_y_escribe_en_datalake(monkeypatch):
    fake_datalake = MagicMock()
    fake_settings = SimpleNamespace(
        datalake_container_gold="gold",
        datalake_container_silver="silver",
        confidence_weights={"VIV_PrestamoDireccionMatricula": 1.0},
        reject_if_encumbrances=False,
    )

    monkeypatch.setattr(activities, "datalake", fake_datalake)
    monkeypatch.setattr(activities, "settings", fake_settings)

    # fija uuid para determinismo
    monkeypatch.setattr(activities.uuid, "uuid4", lambda: "fixed-uuid")

    resultados = [
        {
            "tipo": "estudio_titulos",
            "caso_id": "caso-1",
            "datos": {"PanelFields": [
                {"InternalName": "VIV_PrestamoDireccionMatricula", "Type": "Text", "TextValue": "050C-1"},
            ]},
        },
        {"tipo": "minuta_cancelacion", "caso_id": "caso-1", "datos": {"PanelFields": []}},
        {"tipo": "minuta_constitucion", "caso_id": "caso-1", "datos": {"PanelFields": []}},
    ]

    rutas = activities.activity_sintetizar_resultados(resultados)

    assert "estudio_titulos" in rutas
    assert rutas["estudio_titulos"]["gold"].endswith("fixed-uuid.json")

    # 2 escrituras por tipo (gold + silver)
    assert fake_datalake.write_json.call_count == 6