"""
Pruebas unitarias para functions/triggers.py. Se enfocan en la lógica de activación de los triggers, 
no en la integración con Azure o el procesamiento de PDFs. Se usan mocks para simular los blobs de entrada y para controlar el 
comportamiento de los procesadores.
Las pruebas verifican que los triggers ignoren archivos no PDF o vacíos, que llamen al procesador correcto para un PDF válido, 
y que manejen correctamente las excepciones del procesador."""

import pytest
from unittest.mock import MagicMock, patch

import functions.estudio_titulos_trigger as est
import functions.minuta_cancelacion_trigger as can
import functions.minuta_constitucion_trigger as con


class MockBlob:
    def __init__(self, name, content=b"pdf"):
        self.name = name
        self._content = content

    def read(self):
        return self._content


@pytest.mark.parametrize(
    "mod,processor_attr,fn",
    [
        (est, "EstudioTitulosProcessor", est.process_estudio_titulos),
        (can, "MinutaCancelacionProcessor", can.process_minuta_cancelacion),
        (con, "MinutaConstitucionProcessor", con.process_minuta_constitucion),
    ],
)
def test_trigger_ignora_no_pdf(mod, processor_attr, fn):
    with patch.object(mod, processor_attr) as Proc:
        fn(MockBlob("bronze/x.txt", b"nope"))
        Proc.assert_not_called()


@pytest.mark.parametrize(
    "mod,processor_attr,fn",
    [
        (est, "EstudioTitulosProcessor", est.process_estudio_titulos),
        (can, "MinutaCancelacionProcessor", can.process_minuta_cancelacion),
        (con, "MinutaConstitucionProcessor", con.process_minuta_constitucion),
    ],
)
def test_trigger_ignora_blob_vacio(mod, processor_attr, fn):
    with patch.object(mod, processor_attr) as Proc:
        fn(MockBlob("bronze/x.pdf", b""))
        Proc.assert_not_called()


@pytest.mark.parametrize(
    "mod,processor_attr,fn",
    [
        (est, "EstudioTitulosProcessor", est.process_estudio_titulos),
        (can, "MinutaCancelacionProcessor", can.process_minuta_cancelacion),
        (con, "MinutaConstitucionProcessor", con.process_minuta_constitucion),
    ],
)
def test_trigger_procesa_ok(mod, processor_attr, fn):
    proc = MagicMock()
    proc.process_and_save.return_value = "silver/out.json"

    with patch.object(mod, processor_attr, return_value=proc) as Proc:
        fn(MockBlob("bronze/x.pdf", b"%PDF-1.7"))
        Proc.assert_called_once()
        proc.process_and_save.assert_called_once()


@pytest.mark.parametrize(
    "mod,processor_attr,fn",
    [
        (est, "EstudioTitulosProcessor", est.process_estudio_titulos),
        (can, "MinutaCancelacionProcessor", can.process_minuta_cancelacion),
        (con, "MinutaConstitucionProcessor", con.process_minuta_constitucion),
    ],
)
def test_trigger_procesa_error(mod, processor_attr, fn):
    proc = MagicMock()
    proc.process_and_save.side_effect = RuntimeError("boom")

    with patch.object(mod, processor_attr, return_value=proc):
        with pytest.raises(RuntimeError):
            fn(MockBlob("bronze/x.pdf", b"%PDF-1.7"))