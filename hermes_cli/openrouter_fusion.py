"""OpenRouter Fusion model and plugin configuration helpers."""

from __future__ import annotations

import copy
import shlex
from collections.abc import Callable, Mapping
from typing import Any

FUSION_MODEL_ID = "openrouter/fusion"
FUSION_MODEL_DESCRIPTION = "multi-model analysis with Fusion router"
DEFAULT_FUSION_PRESET = "general-budget"


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "on", "enable", "enabled"}:
            return True
        if raw in {"0", "false", "no", "off", "disable", "disabled"}:
            return False
    return default


def _split_model_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values: list[Any] = []
        for part in value.replace(",", " ").split():
            values.append(part)
    elif isinstance(value, (list, tuple)):
        values = list(value)
    else:
        return []

    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        model = str(item or "").strip()
        if not model or model in seen:
            continue
        seen.add(model)
        out.append(model)
        if len(out) >= 8:
            break
    return out


def normalize_openrouter_fusion_settings(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return validated Fusion plugin settings from an ``openrouter.fusion`` block."""
    fusion = raw if isinstance(raw, Mapping) else {}
    preset = str(fusion.get("preset", DEFAULT_FUSION_PRESET) or "").strip()
    judge_model = str(fusion.get("model", "") or "").strip()

    max_tool_calls = fusion.get("max_tool_calls")
    try:
        max_tool_calls_int = (
            int(max_tool_calls)
            if max_tool_calls is not None and max_tool_calls != ""
            else None
        )
    except (TypeError, ValueError):
        max_tool_calls_int = None
    if max_tool_calls_int is not None and not 1 <= max_tool_calls_int <= 16:
        max_tool_calls_int = None

    return {
        "enabled": _as_bool(fusion.get("enabled"), True),
        "preset": preset,
        "analysis_models": _split_model_values(fusion.get("analysis_models")),
        "model": judge_model,
        "max_tool_calls": max_tool_calls_int,
    }


def get_openrouter_fusion_settings(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Load normalized ``openrouter.fusion`` settings from config.yaml."""
    if config is None:
        try:
            from hermes_cli.config import load_config

            config = load_config() or {}
        except Exception:
            config = {}
    openrouter = config.get("openrouter") if isinstance(config, Mapping) else {}
    fusion = openrouter.get("fusion") if isinstance(openrouter, Mapping) else {}
    return normalize_openrouter_fusion_settings(fusion if isinstance(fusion, Mapping) else {})


def openrouter_show_fusion_model(config: Mapping[str, Any] | None = None) -> bool:
    """Return whether the OpenRouter picker should include ``openrouter/fusion``."""
    if config is None:
        try:
            from hermes_cli.config import load_config

            config = load_config() or {}
        except Exception:
            config = {}
    openrouter = config.get("openrouter") if isinstance(config, Mapping) else {}
    if not isinstance(openrouter, Mapping):
        return True
    return _as_bool(openrouter.get("show_fusion_model"), True)


def apply_openrouter_fusion_model_visibility(
    models: list[tuple[str, str]],
    *,
    config: Mapping[str, Any] | None = None,
) -> list[tuple[str, str]]:
    """Pin or remove the Fusion model alias in an OpenRouter picker list."""
    filtered = [(mid, desc) for mid, desc in models if mid != FUSION_MODEL_ID]
    if not openrouter_show_fusion_model(config):
        return filtered
    insert_at = 1 if filtered else 0
    return [
        *filtered[:insert_at],
        (FUSION_MODEL_ID, FUSION_MODEL_DESCRIPTION),
        *filtered[insert_at:],
    ]


def build_openrouter_fusion_plugin(settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the OpenRouter ``plugins`` entry for the Fusion plugin."""
    normalized = (
        get_openrouter_fusion_settings(settings)
        if settings is None or "openrouter" in settings
        else normalize_openrouter_fusion_settings(settings)
    )
    if not normalized["enabled"]:
        return {"id": "fusion", "enabled": False}

    plugin: dict[str, Any] = {"id": "fusion", "enabled": True}
    if normalized["preset"]:
        plugin["preset"] = normalized["preset"]
    if normalized["analysis_models"]:
        plugin["analysis_models"] = normalized["analysis_models"]
    if normalized["model"]:
        plugin["model"] = normalized["model"]
    if normalized["max_tool_calls"] is not None:
        plugin["max_tool_calls"] = normalized["max_tool_calls"]
    return plugin


def format_openrouter_fusion_status(config: Mapping[str, Any] | None = None) -> str:
    settings = get_openrouter_fusion_settings(config)
    visible = openrouter_show_fusion_model(config)
    panel = ", ".join(settings["analysis_models"]) if settings["analysis_models"] else "(preset/default)"
    judge = settings["model"] or "(preset/default)"
    max_calls = settings["max_tool_calls"] if settings["max_tool_calls"] is not None else "(default)"
    preset = settings["preset"] or "(none)"
    return (
        "Fusion status:\n"
        f"  enabled: {str(settings['enabled']).lower()}\n"
        f"  picker_visible: {str(visible).lower()}\n"
        f"  preset: {preset}\n"
        f"  analysis_models: {panel}\n"
        f"  judge_model: {judge}\n"
        f"  max_tool_calls: {max_calls}"
    )


def _usage() -> str:
    return (
        "Usage: /fusion [status|on|off|show|hide|preset <slug>|"
        "models <model...>|judge <model|clear>|max-tool-calls <1-16|clear>]"
    )


def handle_openrouter_fusion_command(
    arg: str,
    *,
    save_value: Callable[[str, Any], Any] | None = None,
    config: Mapping[str, Any] | None = None,
) -> str:
    """Apply a ``/fusion`` slash command and return user-facing output."""
    if config is None:
        try:
            from hermes_cli.config import load_config

            working_config = load_config() or {}
        except Exception:
            working_config = {}
    else:
        working_config = copy.deepcopy(dict(config))

    try:
        parts = shlex.split(arg or "")
    except ValueError as exc:
        raise ValueError(f"invalid /fusion arguments: {exc}") from exc

    if not parts or parts[0].lower() in {"status", "info"}:
        return format_openrouter_fusion_status(working_config)

    command = parts[0].lower().replace("_", "-")

    def save(path: str, value: Any) -> None:
        current: dict[str, Any] = working_config
        keys = path.split(".")
        for key in keys[:-1]:
            child = current.get(key)
            if not isinstance(child, dict):
                child = {}
                current[key] = child
            current = child
        current[keys[-1]] = value
        if save_value is None:
            return
        result = save_value(path, value)
        if result is False:
            raise RuntimeError(f"failed to save {path}")

    if command in {"on", "enable", "enabled"}:
        save("openrouter.fusion.enabled", True)
        return "Fusion enabled.\n" + format_openrouter_fusion_status(working_config)
    if command in {"off", "disable", "disabled"}:
        save("openrouter.fusion.enabled", False)
        return "Fusion disabled.\n" + format_openrouter_fusion_status(working_config)
    if command == "show":
        save("openrouter.show_fusion_model", True)
        return "Fusion model shown in OpenRouter picker.\n" + format_openrouter_fusion_status(working_config)
    if command == "hide":
        save("openrouter.show_fusion_model", False)
        return "Fusion model hidden from OpenRouter picker.\n" + format_openrouter_fusion_status(working_config)
    if command == "preset":
        if len(parts) != 2 or not parts[1].strip():
            raise ValueError(_usage())
        save("openrouter.fusion.preset", parts[1].strip())
        save("openrouter.fusion.analysis_models", [])
        save("openrouter.fusion.model", "")
        return f"Fusion preset set to {parts[1].strip()}.\n" + format_openrouter_fusion_status(working_config)
    if command in {"models", "analysis-models", "panel"}:
        models = _split_model_values(parts[1:])
        if not 1 <= len(models) <= 8:
            raise ValueError("Usage: /fusion models <1-8 model ids>")
        save("openrouter.fusion.analysis_models", models)
        save("openrouter.fusion.preset", "")
        return "Fusion analysis models updated.\n" + format_openrouter_fusion_status(working_config)
    if command in {"judge", "model"}:
        if len(parts) != 2:
            raise ValueError("Usage: /fusion judge <model|clear>")
        value = "" if parts[1].lower() in {"clear", "none", "default"} else parts[1].strip()
        save("openrouter.fusion.model", value)
        return "Fusion judge model updated.\n" + format_openrouter_fusion_status(working_config)
    if command in {"max-tool-calls", "max-calls"}:
        if len(parts) != 2:
            raise ValueError("Usage: /fusion max-tool-calls <1-16|clear>")
        if parts[1].lower() in {"clear", "none", "default"}:
            save("openrouter.fusion.max_tool_calls", "")
            return "Fusion max tool calls reset.\n" + format_openrouter_fusion_status(working_config)
        try:
            value = int(parts[1])
        except ValueError as exc:
            raise ValueError("max-tool-calls must be an integer from 1 to 16") from exc
        if not 1 <= value <= 16:
            raise ValueError("max-tool-calls must be from 1 to 16")
        save("openrouter.fusion.max_tool_calls", value)
        return "Fusion max tool calls updated.\n" + format_openrouter_fusion_status(working_config)

    raise ValueError(_usage())
