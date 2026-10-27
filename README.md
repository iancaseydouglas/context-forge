# LLM Context Forge

Functional Python pipeline over immutable state that reduces three repos to their API surface, merges them into one XML context, and caches it in Gemini, letting coding assistants write against large libraries without ingesting full source.

**Stack:** Python 3.11+ · Pydantic v2 · toolz · Typer · Rich · Repomix · mypy/stubgen · Gemini context caching

## Overview

Assistants need the public APIs they call, not the implementation behind them. Context Forge reduces each repo by role, merges the results into a single XML context, caches it in Gemini, and writes the cache ID to the active repo's IDE rules.

Target workflow: quant. VectorBT Pro, Lightweight Charts, strategy repo.

## Reduction by repo

| Repo | Role | Strategy | Tooling | Kept |
| --- | --- | --- | --- | --- |
| Strategy | read/write | `full` | Repomix | Everything |
| VectorBT Pro | reference | `stub` | stubgen, Repomix | Type signatures |
| Lightweight Charts | reference | `compress` | Repomix `--compress` | Interfaces, JSDoc |

## Pipeline

```
3 repo paths -> ForgeState (immutable)
  -> generate_vbt_stubs    # stubgen on VectorBT Pro
  -> pack_repositories     # Repomix x3, merge to one XML
  -> upload_to_gemini      # explicit cache, 8h TTL
  -> cache ID -> .antigravity/rules.md
```

Merged XML tags each section so the model knows its fidelity:

```xml
<context_root>
  <library name="vectorbtpro" type="stubbed_reference">...</library>
  <library name="lightweight-charts" type="compressed_reference">...</library>
  <workspace name="active_repository" type="full_fidelity">...</workspace>
</context_root>
```

## Design

- **Pure core, effectful ops.** `core/`: frozen Pydantic models, no I/O. `ops/`: stages of type `ForgeState -> ForgeState`.
- **Immutable state.** Stages return copies via `model_copy`.
- **Composition.** `pipe(state, generate_vbt_stubs, pack_repositories, upload_to_gemini)`
- **Short-circuit errors.** A failing stage calls `state.fail(...)`; later stages pass state through. CLI reports once, exits non-zero.
- **Minimal footprint.** Scratch in `/tmp/forge`. Only `.antigravity/rules.md` is written to your repos.

## Usage

Requires Python 3.11+, Node.js, a Google API key, and a licensed VectorBT Pro.

```bash
poetry install
npm install -g repomix
export GOOGLE_API_KEY="..."

poetry run forge \
  --active /path/to/strategy-repo \
  --vbt /path/to/dir-containing-vectorbtpro \
  --charts /path/to/lightweight-charts
```

`--vbt` is the directory *containing* the `vectorbtpro` package, not the package itself.

## Layout

```
src/context_forge/
├── main.py              # CLI
├── core/state.py        # ForgeState, RepoConfig
└── ops/
    ├── compression.py   # stubgen, Repomix, merge
    └── gateway.py       # Gemini cache upload
```