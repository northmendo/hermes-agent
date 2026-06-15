def test_openrouter_model_list_source_default_is_curated(monkeypatch):
    from hermes_cli import config, models

    monkeypatch.setattr(config, "load_config", lambda: {"openrouter": {}})

    assert models.get_openrouter_model_list_source() == "curated"
