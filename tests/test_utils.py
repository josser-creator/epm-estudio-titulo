import datetime as dt

from utils.business_days import _ensure_utc, business_days_between
from utils.json_cleaner import JsonCleaner


def test_ensure_utc_convierte_naive_a_utc():
    value = dt.datetime(2026, 3, 30, 10, 15)
    result = _ensure_utc(value)
    assert result.tzinfo == dt.timezone.utc
    assert result.hour == 10


def test_business_days_between_excluye_fin_de_semana():
    start = dt.datetime(2026, 3, 27, 8, 0, tzinfo=dt.timezone.utc)
    end = dt.datetime(2026, 3, 31, 8, 0, tzinfo=dt.timezone.utc)
    assert business_days_between(start, end) == 2


def test_business_days_between_cuando_start_es_mayor_retorna_cero():
    start = dt.datetime(2026, 4, 2, 8, 0)
    end = dt.datetime(2026, 4, 1, 8, 0)
    assert business_days_between(start, end) == 0


def test_json_cleaner_clean_currency_detecta_formato_colombiano():
    result = JsonCleaner.clean_currency("$50.000.000,25 COP")
    assert result == {"valor": 50000000.25, "moneda": "COP", "original": "$50.000.000,25 COP"}


def test_json_cleaner_clean_identification_detecta_cc():
    result = JsonCleaner.clean_identification("C.C. 1.234.567")
    assert result["tipo"] == "CC"
    assert result["numero"] == "1234567"
    assert result["original"] == "C.C. 1.234.567"


def test_json_cleaner_remove_empty_values_limpia_recursivamente():
    data = {
        "a": "valor", "b": "", "c": None, "d": [], "e": {},
        "f": {"ok": 1, "vacio": None},
        "g": [1, None, "", {"x": None, "y": "z"}],
    }
    result = JsonCleaner.remove_empty_values(data)
    assert result == {"a": "valor", "f": {"ok": 1}, "g": [1, {"y": "z"}]}


def test_json_cleaner_extract_json_from_markdown_code_block():
    text = 'Respuesta\n```json\n{"campo":"valor"}\n```\n'
    assert JsonCleaner.extract_json_from_text(text) == {"campo": "valor"}
