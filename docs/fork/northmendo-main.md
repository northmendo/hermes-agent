# Northmendo Fork Main

This fork uses `northmendo/main` as the install and update channel. A normal
fork install should behave like upstream Hermes: `hermes update` fetches and
pulls `origin/<branch>`, with `main` as the default branch.

## Install Commands

Windows:

```powershell
iex (irm https://raw.githubusercontent.com/northmendo/hermes-agent/main/scripts/install.ps1)
```

macOS, Linux, and WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/northmendo/hermes-agent/main/scripts/install.sh | bash
```

## Branch Layout

| Branch | Purpose | Upstream PR? |
| --- | --- | --- |
| `main` | Fork install/update channel | No |
| `feat/openrouter-model-list-source` | OpenRouter model source picker (`curated`, `all`, `user`) | Yes |
| `feat/builtin-reasoning-status-bar` | Built-in reasoning effort in status bar | Yes |
| `feat/plugin-logical-id-dedupe` | Plugin dedupe by logical identity and idempotent hooks | Yes |

Fork-only commits on `main` cover installer defaults, fork README/docs, and the
update channel. Do not PR those commits upstream.

## Retired Branches

`feat/northmendo-qol-bundle`, `personal/northmendo-update-source`, and
`feat/local-models-small-setups` are obsolete once `main` is confirmed working.
`feat/fork-python-3_14-support` is paused/rejected for now because upstream
still intentionally caps Python at `<3.14` pending wheel support for Rust-backed
dependencies.

## Sync Process

The `Upstream Sync Check` workflow rebases `northmendo/main` onto
`NousResearch/main` and fails on conflicts. Resolve conflicts manually, rerun
the focused update/install tests, then push `main`.
