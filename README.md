# Context Forge ⚒️

**TL;DR:** Context Forge shrinks three codebases by role, merges them into one XML context, and caches it in Gemini, so a coding assistant can write against large libraries without reading their full source.

A split-state functional orchestrator that prepares large codebases for LLM context caching.

Python 3.11+ · Pydantic v2 · toolz · Typer · Rich · Repomix · mypy/stubgen · Gemini context caching

## Overview

Coding assistants need the APIs they write against, not the full source behind them. Context Forge shrinks three repos by role, merges them into one XML context, caches it in Gemini, and writes the cache ID into the active repo's IDE rules.

Built for a quant workflow: VectorBT Pro, Lightweight Charts, and a strategy repo.

## Strategy per repo

| Repository | Role | Strategy | Tooling | Kept |
| --- | --- | --- | --- | --- |
| Strategy repo | read/write | `full` | Repomix | Everything |
| VectorBT Pro | reference | `stub` | stubgen, Repomix | Type signatures only |
| Lightweight Charts | reference | `compress` | Repomix `--compress` | Interfaces and JSDoc |

## Pipeline

```
3 repo paths -> ForgeState (immutable)
  -> generate_vbt_stubs    # stubgen on VectorBT Pro
  -> pack_repositories     # Repomix x3, merge to one XML
  -> upload_to_gemini      # explicit cache, 8h TTL
  -> cache ID -> .antigravity/rules.md
```

The merged XML labels each section for the model:

```xml
<context_root>
  <library name="vectorbtpro" type="stubbed_reference">...</library>
  <library name="lightweight-charts" type="compressed_reference">...</library>
  <workspace name="active_repository" type="full_fidelity">...</workspace>
</context_root>
```

## Design

- **Pure core, effectful ops.** `core/` holds frozen Pydantic models and no I/O. `ops/` holds stages shaped `ForgeState -> ForgeState`.
- **Immutable state.** Stages return copies via `model_copy`. Never mutation.
- **One expression.** `pipe(state, generate_vbt_stubs, pack_repositories, upload_to_gemini)`
- **Short-circuit errors.** A failed stage calls `state.fail(...)`; later stages pass the state through. The CLI reports once and exits non-zero.
- **Clean footprint.** Scratch files live in `/tmp/forge`. Only `.antigravity/rules.md` touches your repos.

## Skills shown

Functional pipeline design · Pydantic v2 state modeling · Typer/Rich CLIs · orchestrating external tools · LLM context caching · Poetry `src/` packaging

## Run

Needs Python 3.11+, Node.js, a Google API key, and a licensed VectorBT Pro.

```bash
poetry install
npm install -g repomix
export GOOGLE_API_KEY="..."

poetry run forge \
  --active /path/to/strategy-repo \
  --vbt /path/to/dir-containing-vectorbtpro \
  --charts /path/to/lightweight-charts
```

`--vbt` is the directory that *contains* the `vectorbtpro` package.

## Structure

```
src/context_forge/
├── main.py              # CLI
├── core/state.py        # ForgeState, RepoConfig
└── ops/
    ├── compression.py   # stubgen, Repomix, merge
    └── gateway.py       # Gemini cache upload
```

## Roadmap

- Configurable repo targets
- Real token counting with a budget guard
- Cache reuse and refresh
- Per-stage unit tests

