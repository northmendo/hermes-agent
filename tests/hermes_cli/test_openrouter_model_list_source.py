def test_openrouter_model_list_source_default_is_curated(monkeypatch):
    from hermes_cli import config, models

    monkeypatch.setattr(config, "load_config", lambda: {"openrouter": {}})

    assert models.get_openrouter_model_list_source() == "curated"


def test_resolve_openrouter_api_key_from_env_file_helper(monkeypatch):
    from hermes_cli import config, models

    monkeypatch.setattr(config, "get_env_value", lambda name: "sk-or-env" if name == "OPENROUTER_API_KEY" else "")

    assert models.resolve_openrouter_api_key_for_models_user() == "sk-or-env"


def test_resolve_openrouter_api_key_from_credential_pool(monkeypatch):
    from hermes_cli import config, models

    monkeypatch.setattr(config, "get_env_value", lambda name: "")

    class Entry:
        access_token = "sk-or-pool"
        runtime_api_key = ""

    class Pool:
        def has_credentials(self):
            return True
        def peek(self):
            return Entry()

    monkeypatch.setitem(__import__("sys").modules, "agent.credential_pool", type("M", (), {"load_pool": staticmethod(lambda provider: Pool())}))

    assert models.resolve_openrouter_api_key_for_models_user() == "sk-or-pool"


import json


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_fetch_openrouter_live_items_uses_user_endpoint_and_auth(monkeypatch):
    from hermes_cli import models

    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["auth"] = req.headers.get("Authorization")
        return _FakeResponse({"data": [{"id": "user/model", "supported_parameters": ["tools"], "pricing": {"prompt": "0", "completion": "0"}}]})

    monkeypatch.setattr(models.urllib.request, "urlopen", fake_urlopen)

    items = models.fetch_openrouter_live_items("user", api_key="sk-test", timeout=1)

    assert seen["url"] == "https://openrouter.ai/api/v1/models/user"
    assert seen["auth"] == "Bearer sk-test"
    assert items[0]["id"] == "user/model"


def test_fetch_openrouter_live_items_uses_public_endpoint_for_all(monkeypatch):
    from hermes_cli import models

    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["auth"] = req.headers.get("Authorization")
        return _FakeResponse({"data": [{"id": "public/model", "supported_parameters": ["tools"], "pricing": {"prompt": "0", "completion": "0"}}]})

    monkeypatch.setattr(models.urllib.request, "urlopen", fake_urlopen)

    items = models.fetch_openrouter_live_items("all", timeout=1)

    assert seen["url"] == "https://openrouter.ai/api/v1/models"
    assert seen["auth"] is None
    assert items[0]["id"] == "public/model"


def test_fetch_openrouter_models_all_uses_live_api_order(monkeypatch):
    from hermes_cli import models

    monkeypatch.setattr(models, "get_openrouter_model_list_source", lambda: "all")
    monkeypatch.setattr(models, "fetch_openrouter_live_items", lambda source, **kwargs: [
        {"id": "z/model", "supported_parameters": ["tools"], "pricing": {"prompt": "0.1", "completion": "0.2"}},
        {"id": "a/free", "supported_parameters": ["tools"], "pricing": {"prompt": "0", "completion": "0"}},
        {"id": "no/tools", "supported_parameters": ["temperature"], "pricing": {"prompt": "0", "completion": "0"}},
    ])
    models._openrouter_catalog_cache = None

    assert models.fetch_openrouter_models(force_refresh=True) == [
        ("z/model", ""),
        ("openrouter/fusion", "multi-model analysis with Fusion router"),
        ("a/free", "free"),
    ]


def test_fetch_openrouter_models_user_uses_user_filtered_api_order(monkeypatch):
    from hermes_cli import models

    monkeypatch.setattr(models, "get_openrouter_model_list_source", lambda: "user")
    monkeypatch.setattr(models, "resolve_openrouter_api_key_for_models_user", lambda: "sk-test")
    monkeypatch.setattr(models, "fetch_openrouter_live_items", lambda source, **kwargs: [
        {"id": "my/model", "supported_parameters": ["tools"], "pricing": {"prompt": "0", "completion": "0"}},
    ])
    models._openrouter_catalog_cache = None

    assert models.fetch_openrouter_models(force_refresh=True) == [
        ("my/model", "free"),
        ("openrouter/fusion", "multi-model analysis with Fusion router"),
    ]


def test_fetch_openrouter_models_can_hide_pinned_fusion(monkeypatch):
    from hermes_cli import models

    monkeypatch.setattr(models, "get_openrouter_model_list_source", lambda: "all")
    monkeypatch.setattr(
        "hermes_cli.openrouter_fusion.openrouter_show_fusion_model",
        lambda config=None: False,
    )
    monkeypatch.setattr(models, "fetch_openrouter_live_items", lambda source, **kwargs: [
        {"id": "z/model", "supported_parameters": ["tools"], "pricing": {"prompt": "0.1", "completion": "0.2"}},
    ])
    models._openrouter_catalog_cache = None

    assert models.fetch_openrouter_models(force_refresh=True) == [("z/model", "")]


def test_save_openrouter_model_list_source_updates_config(monkeypatch):
    from hermes_cli import config, models

    state = {"openrouter": {"response_cache": True}}
    monkeypatch.setattr(config, "load_config", lambda: state.copy())
    saved = {}
    monkeypatch.setattr(config, "save_config", lambda cfg: saved.update(cfg))

    models.save_openrouter_model_list_source("user")

    assert saved["openrouter"]["model_list_source"] == "user"
