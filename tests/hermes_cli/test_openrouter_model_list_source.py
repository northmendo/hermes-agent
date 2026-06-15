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
