import pytest
from unittest.mock import MagicMock, patch

import function_app


# =========================================================
# Test detectar_tipo_por_nombre
# =========================================================

@pytest.mark.parametrize(
    "nombre,esperado",
    [
        ("estudio de titulos.pdf", "EstudioTitulos"),
        ("ESTUDIO_DE_TITULOS.PDF", "EstudioTitulos"),
        ("minuta_cancelacion_123.pdf", "MinutaCancelacion"),
        ("minuta_constitucion.pdf", "MinutaConstitucion"),
        ("documento_desconocido.pdf", None),
    ],
)
def test_detectar_tipo_por_nombre(nombre, esperado):
    resultado = function_app.detectar_tipo_por_nombre(nombre)
    assert resultado == esperado


# =========================================================
# Test persistir_resultados
# =========================================================

@patch("function_app.datalake")
@patch("function_app.cosmos")
def test_persistir_resultados(mock_cosmos, mock_datalake):
    mock_datalake.write_json.return_value = "silver/test/path.json"

    extracted = {"campo": "valor"}

    result = function_app.persistir_resultados(
        extracted_data=extracted,
        caso_id="caso123",
        process_id="proc123",
        tipo_documento="estudio_titulos",
        archivo_origen="archivo.pdf",
        processor_name="ProcessorTest",
        subpath="conecta/vivienda/estudio-titulos"
    )

    assert result == "conecta/vivienda/estudio-titulos/caso123/proc123.json"

    mock_datalake.write_json.assert_called_once()
    mock_cosmos.upsert_document.assert_called_once()


# =========================================================
# Mock Blob InputStream (simula Azure Blob)
# =========================================================

class MockBlob:
    def __init__(self, name, content=b"pdfcontent"):
        self.name = name
        self._content = content

    def read(self):
        return self._content

    @property
    def length(self):
        return len(self._content)


# =========================================================
# Test process_blob correcto
# =========================================================

@patch("function_app.persistir_resultados")
@patch("processors.base_processor.DocumentIntelligenceService")
def test_process_blob_success(mock_doc_intelligence, mock_persist):
    # Mock del servicio de Document Intelligence
    mock_doc_intelligence_instance = MagicMock()
    mock_doc_intelligence_instance.analyze_document.return_value = {"analisis": "completado"}
    mock_doc_intelligence.return_value = mock_doc_intelligence_instance

    # Mock del processor
    processor = MagicMock(spec=function_app.EstudioTitulosProcessor)
    processor.process.return_value = {"resultado": "ok"}
    
    # Creamos una clase mock que devuelva nuestra instancia de processor
    MockProcessorClass = MagicMock(return_value=processor)
    
    # Patch la clase del procesador en BLOB_TIPO_MAP
    with patch.dict("function_app.BLOB_TIPO_MAP", {
        "EstudioTitulos": (
            "estudio_titulos",
            MockProcessorClass,  # Usamos la clase mock en lugar de MagicMock directo
            "VIV-514.2_1901",
            "conecta/vivienda/estudio-titulos",
        )
    }):
        blob = MockBlob("bronze/conecta/vivienda/1/estudio_de_titulos.pdf")

        # Pasamos la clave del tipo, no el processor directamente
        function_app.process_blob(
            blob,
            "EstudioTitulos"  # Pasamos el string key, no el processor
        )

        # Verificamos que se creó el processor y se llamó a process
        MockProcessorClass.assert_called_once()
        processor.process.assert_called_once()
        mock_persist.assert_called_once()


# =========================================================
# Test ignorar archivos no PDF
# =========================================================

def test_process_blob_ignore_non_pdf():
    # Creamos un mock para la clase del processor
    MockProcessorClass = MagicMock()
    
    with patch.dict("function_app.BLOB_TIPO_MAP", {
        "EstudioTitulos": (
            "estudio_titulos",
            MockProcessorClass,
            "VIV-514.2_1901",
            "conecta/vivienda/estudio-titulos",
        )
    }):
        blob = MockBlob("bronze/conecta/vivienda/1/documento.txt")

        function_app.process_blob(
            blob,
            "EstudioTitulos"
        )

        # Verificamos que NO se creó el processor
        MockProcessorClass.assert_not_called()


# =========================================================
# Test blob vacío
# =========================================================

def test_process_blob_empty_blob():
    # Creamos un mock para la clase del processor
    MockProcessorClass = MagicMock()
    
    with patch.dict("function_app.BLOB_TIPO_MAP", {
        "EstudioTitulos": (
            "estudio_titulos",
            MockProcessorClass,
            "VIV-514.2_1901",
            "conecta/vivienda/estudio-titulos",
        )
    }):
        blob = MockBlob(
            "bronze/conecta/vivienda/1/estudio_de_titulos.pdf",
            content=b""
        )

        function_app.process_blob(
            blob,
            "EstudioTitulos"
        )

        # Verificamos que NO se creó el processor
        MockProcessorClass.assert_not_called()


# =========================================================
# Test process_blob con error en procesamiento
# =========================================================

@patch("function_app.persistir_resultados")
@patch("processors.base_processor.DocumentIntelligenceService")
def test_process_blob_error(mock_doc_intelligence, mock_persist):
    # Mock del servicio de Document Intelligence
    mock_doc_intelligence_instance = MagicMock()
    mock_doc_intelligence_instance.analyze_document.return_value = {"analisis": "completado"}
    mock_doc_intelligence.return_value = mock_doc_intelligence_instance

    # Mock del processor que lanza excepción
    processor = MagicMock(spec=function_app.EstudioTitulosProcessor)
    processor.process.side_effect = Exception("Error simulado en procesamiento")
    
    # Creamos una clase mock que devuelva nuestra instancia de processor
    MockProcessorClass = MagicMock(return_value=processor)

    with patch.dict("function_app.BLOB_TIPO_MAP", {
        "EstudioTitulos": (
            "estudio_titulos",
            MockProcessorClass,
            "VIV-514.2_1901",
            "conecta/vivienda/estudio-titulos",
        )
    }):
        blob = MockBlob("bronze/conecta/vivienda/1/estudio_de_titulos.pdf")

        with pytest.raises(Exception) as exc_info:
            function_app.process_blob(
                blob,
                "EstudioTitulos"
            )

        assert "Error simulado en procesamiento" in str(exc_info.value)
        MockProcessorClass.assert_called_once()
        processor.process.assert_called_once()
        mock_persist.assert_not_called()


# =========================================================
# Test detectar_tipo_por_nombre casos borde
# =========================================================

@pytest.mark.parametrize(
    "nombre,esperado",
    [
        ("", None),
        (".pdf", None),
        ("estudio_de_titulos_sin_extension", "EstudioTitulos"),
        ("DOCUMENTO_CANCELACION.PDF", "MinutaCancelacion"),
        ("MINUTA CONSTITUCION 2024.PDF", "MinutaConstitucion"),
        ("mezcla_estudio_de_titulos_y_cancelacion.pdf", "EstudioTitulos"),  # Primera coincidencia
    ],
)
def test_detectar_tipo_por_nombre_casos_borde(nombre, esperado):
    resultado = function_app.detectar_tipo_por_nombre(nombre)
    assert resultado == esperado