import os
import sys
import types


def _noop_decorator(*args, **kwargs):
    def decorator(fn):
        return fn
    return decorator


class _MockHttpResponse:
    def __init__(self, body=None, status_code=200):
        self.body = body
        self.status_code = status_code


class _MockHttpRequest:
    def __init__(self, route_params=None):
        self.route_params = route_params or {}


class _MockInputStream:
    def __init__(self, name="", content=b""):
        self.name = name
        self._content = content

    def read(self):
        return self._content


class _MockDFApp:
    def activity_trigger(self, *args, **kwargs):
        return _noop_decorator(*args, **kwargs)

    def orchestration_trigger(self, *args, **kwargs):
        return _noop_decorator(*args, **kwargs)

    def route(self, *args, **kwargs):
        return _noop_decorator(*args, **kwargs)

    def durable_client_input(self, *args, **kwargs):
        return _noop_decorator(*args, **kwargs)

    def blob_trigger(self, *args, **kwargs):
        return _noop_decorator(*args, **kwargs)

    def timer_trigger(self, *args, **kwargs):
        return _noop_decorator(*args, **kwargs)


class _MockDataLakeServiceClient:
    def __init__(self, *args, **kwargs):
        pass

    def get_file_system_client(self, *args, **kwargs):
        return types.SimpleNamespace(
            get_paths=lambda *a, **k: [],
            get_file_client=lambda *a, **k: types.SimpleNamespace(delete_file=lambda: None),
            get_directory_client=lambda *a, **k: types.SimpleNamespace(create_directory=lambda: None),
        )


class _MockAzureKeyCredential:
    def __init__(self, *args, **kwargs):
        pass


class _MockDocumentAnalysisClient:
    def __init__(self, *args, **kwargs):
        pass

    def begin_analyze_document(self, *args, **kwargs):
        class _Poller:
            def result(self):
                return types.SimpleNamespace(content="", pages=[], tables=[], paragraphs=[])
        return _Poller()


class _MockPartitionKey:
    def __init__(self, path=None):
        self.path = path


class _MockCosmosClient:
    def __init__(self, *args, **kwargs):
        pass

    def create_database_if_not_exists(self, id=None):
        return types.SimpleNamespace(
            create_container_if_not_exists=lambda **kwargs: types.SimpleNamespace(
                upsert_item=lambda body: body,
                read_item=lambda item, partition_key: {"id": item, "tipoDocumento": partition_key},
            )
        )

    def get_database_account(self):
        return {"ok": True}


class _MockAzureOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **kwargs: types.SimpleNamespace(
                    choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="{}"))]
                )
            )
        )


env = {
    "DATALAKE_ACCOUNT_NAME": "dummyaccount",
    "DATALAKE_ACCOUNT_KEY": "dummykey",
    "DOCUMENT_INTELLIGENCE_ENDPOINT": "https://dummy-doc.cognitiveservices.azure.com/",
    "DOCUMENT_INTELLIGENCE_KEY": "dummy-doc-key",
    "AZURE_OPENAI_ENDPOINT": "https://dummy-openai.openai.azure.com/",
    "AZURE_OPENAI_KEY": "dummy-openai-key",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4o",
    "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
    "COSMOS_ENDPOINT": "https://dummy-cosmos.documents.azure.com:443/",
    "COSMOS_KEY": "dummy-cosmos-key",
}
for key, value in env.items():
    os.environ.setdefault(key, value)

azure_module = types.ModuleType("azure")
azure_functions = types.ModuleType("azure.functions")
azure_functions.HttpResponse = _MockHttpResponse
azure_functions.HttpRequest = _MockHttpRequest
azure_functions.InputStream = _MockInputStream
azure_functions.TimerRequest = object

azure_durable = types.ModuleType("azure.durable_functions")
azure_durable.DFApp = _MockDFApp
azure_durable.DurableOrchestrationContext = object

azure_storage = types.ModuleType("azure.storage")
azure_storage_filedatalake = types.ModuleType("azure.storage.filedatalake")
azure_storage_filedatalake.DataLakeServiceClient = _MockDataLakeServiceClient

azure_core = types.ModuleType("azure.core")
azure_core_credentials = types.ModuleType("azure.core.credentials")
azure_core_credentials.AzureKeyCredential = _MockAzureKeyCredential

azure_ai = types.ModuleType("azure.ai")
azure_ai_formrecognizer = types.ModuleType("azure.ai.formrecognizer")
azure_ai_formrecognizer.DocumentAnalysisClient = _MockDocumentAnalysisClient

azure_cosmos = types.ModuleType("azure.cosmos")
azure_cosmos.CosmosClient = _MockCosmosClient
azure_cosmos.PartitionKey = _MockPartitionKey
azure_cosmos.exceptions = types.SimpleNamespace(CosmosResourceNotFoundError=KeyError)

openai_module = types.ModuleType("openai")
openai_module.AzureOpenAI = _MockAzureOpenAI

sys.modules.setdefault("azure", azure_module)
sys.modules.setdefault("azure.functions", azure_functions)
sys.modules.setdefault("azure.durable_functions", azure_durable)
sys.modules.setdefault("azure.storage", azure_storage)
sys.modules.setdefault("azure.storage.filedatalake", azure_storage_filedatalake)
sys.modules.setdefault("azure.core", azure_core)
sys.modules.setdefault("azure.core.credentials", azure_core_credentials)
sys.modules.setdefault("azure.ai", azure_ai)
sys.modules.setdefault("azure.ai.formrecognizer", azure_ai_formrecognizer)
sys.modules.setdefault("azure.cosmos", azure_cosmos)
sys.modules.setdefault("openai", openai_module)
