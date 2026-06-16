# Northmendo QoL Bundle (personal install)

This document explains the fork-specific branches used for the personal `northmendo/hermes-agent` install.

## Branch layout

| Branch | Purpose | Upstream PR? |
|---|---|---|
| `feat/openrouter-model-list-source` | OpenRouter model source picker (`curated`/`all`/`user`) | Yes |
| `feat/builtin-reasoning-status-bar` | Built-in reasoning effort in status bar | Yes |
| `feat/plugin-logical-id-dedupe` | Plugin dedupe by `logical_id` + idempotent hooks | Yes |
| `feat/fork-python-3_14-support` | Python 3.14 package metadata | No (fork QoL) |
| `personal/northmendo-update-source` | Fork-specific `hermes update` source | **Never** |
| `feat/northmendo-qol-bundle` | Install-everything bundle branch | **Never** |

## How the bundle is built

```bash
git checkout main
git checkout -B feat/northmendo-qol-bundle
git merge --no-ff feat/openrouter-model-list-source \
          feat/builtin-reasoning-status-bar \
          feat/plugin-logical-id-dedupe \
          feat/fork-python-3_14-support \
          personal/northmendo-update-source
```

## Install command

```bash
pip install git+https://github.com/northmendo/hermes-agent.git@feat/northmendo-qol-bundle
```

## Updating

On a bundle install, `hermes update` will reinstall from the bundle branch. If an old upstream git clone exists at `$HERMES_HOME/hermes-agent`, `hermes update` will offer to archive it.

## Syncing with upstream

To pull latest NousResearch changes into the focused feature branches:

```bash
git fetch upstream
git rebase upstream/main
```

Then rebuild the bundle branch as shown above.
