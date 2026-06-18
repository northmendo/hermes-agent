from hermes_cli.openrouter_fusion import (
    FUSION_MODEL_ID,
    apply_openrouter_fusion_model_visibility,
    build_openrouter_fusion_plugin,
    handle_openrouter_fusion_command,
)


def test_default_plugin_uses_general_budget_preset():
    assert build_openrouter_fusion_plugin({"preset": "general-budget"}) == {
        "id": "fusion",
        "enabled": True,
        "preset": "general-budget",
    }


def test_disabled_plugin_emits_bypass_only():
    assert build_openrouter_fusion_plugin({"enabled": False, "preset": "general-high"}) == {
        "id": "fusion",
        "enabled": False,
    }


def test_custom_preset_slug_passes_through():
    assert build_openrouter_fusion_plugin({"preset": "my-custom-slug"})["preset"] == "my-custom-slug"


def test_analysis_models_and_judge_override_preset_fields():
    plugin = build_openrouter_fusion_plugin(
        {
            "preset": "general-high",
            "analysis_models": ["~anthropic/claude-opus-latest", "~openai/gpt-latest"],
            "model": "~openai/gpt-latest",
            "max_tool_calls": "8",
        }
    )

    assert plugin == {
        "id": "fusion",
        "enabled": True,
        "preset": "general-high",
        "analysis_models": ["~anthropic/claude-opus-latest", "~openai/gpt-latest"],
        "model": "~openai/gpt-latest",
        "max_tool_calls": 8,
    }


def test_model_visibility_pins_fusion_after_first_model():
    models = [("a/model", ""), ("b/model", "")]

    assert apply_openrouter_fusion_model_visibility(models) == [
        ("a/model", ""),
        (FUSION_MODEL_ID, "multi-model analysis with Fusion router"),
        ("b/model", ""),
    ]


def test_model_visibility_can_hide_fusion():
    models = [("a/model", ""), (FUSION_MODEL_ID, "old")]

    assert apply_openrouter_fusion_model_visibility(
        models,
        config={"openrouter": {"show_fusion_model": False}},
    ) == [("a/model", "")]


def test_fusion_models_command_sets_panel_and_clears_preset():
    saved = {}

    output = handle_openrouter_fusion_command(
        "models ~anthropic/claude-opus-latest ~openai/gpt-latest",
        save_value=lambda key, value: saved.setdefault(key, value),
        config={"openrouter": {"fusion": {"preset": "general-budget"}}},
    )

    assert "analysis models updated" in output
    assert saved["openrouter.fusion.analysis_models"] == [
        "~anthropic/claude-opus-latest",
        "~openai/gpt-latest",
    ]
    assert saved["openrouter.fusion.preset"] == ""


def test_fusion_preset_command_accepts_custom_slug_and_clears_overrides():
    saved = {}

    handle_openrouter_fusion_command(
        "preset my-custom-slug",
        save_value=lambda key, value: saved.setdefault(key, value),
        config={"openrouter": {"fusion": {"analysis_models": ["a"], "model": "judge"}}},
    )

    assert saved["openrouter.fusion.preset"] == "my-custom-slug"
    assert saved["openrouter.fusion.analysis_models"] == []
    assert saved["openrouter.fusion.model"] == ""
