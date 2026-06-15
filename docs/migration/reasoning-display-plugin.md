# Reasoning status display is now built-in

The CLI status bar now appends the active reasoning effort (e.g. `[medium]`) to the model short name whenever reasoning is enabled. This makes any external "reasoning display" plugin that manipulated the status bar redundant.

## What changed

- `HermesCLI._get_status_bar_snapshot()` reads `self.reasoning_config` and, when reasoning is enabled, appends `[<effort>]` to `model_short`.
- The suffix is added idempotently: calling `_get_status_bar_snapshot()` repeatedly will not create `model[high][high]`.

## Migration

If you previously installed a third-party plugin to show reasoning effort in the status bar:

1. Remove or disable the plugin via `hermes plugins`.
2. Enable reasoning as usual with `/reasoning` or `display.show_reasoning: true`.
3. The effort level will appear in the status bar automatically.

## Plugin authors

Plugins that previously hooked the status bar to render reasoning effort should stop doing so. Use the `reasoning_config` state already present on the CLI object, or register a different hook if you need to react to reasoning changes.
