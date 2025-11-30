
# Context Forge ⚒️

**A Split-State Functional Orchestrator for Gemini 3 Context Caching.**

This tool hydrates a "Quant-State" development environment by processing local repositories and uploading them to Google Vertex AI / Gemini Context Cache.

## Features

* **VectorBT Pro Handling**: Uses `stubgen` to strip massive Numba implementation details while keeping type signatures for the LLM.
* **Lightweight Charts Handling**: Uses `repomix --compress` (Tree-sitter) to keep TypeScript interfaces but remove logic.
* **Gemini 3 Ultra**: Uploads the combined context to the 2M+ token window with explicit caching.

## Installation

### Dependencies

```bash
pip install poetry
poetry install
npm install -g repomix
```

## Usage

Set your Google API Key:

```bash
export GOOGLE_API_KEY="AIzaSy..."
```

Run the Forge:

```bash
poetry run forge \
  --active /path/to/my-strategy-repo \
  --vbt /path/to/vectorbtpro_library \
  --charts /path/to/lightweight-charts_library
```

The tool will output a **Cache ID** and automatically inject it into your active repo's `.antigravity/rules.md`.

---

### Implementation Notes

1. **VBT Stubbing**: The `generate_vbt_stubs` function assumes `vectorbtpro` is the folder name inside the path you provide. Since VBT Pro is proprietary, ensure the path you pass points to the root directory that *contains* the `vectorbtpro` package folder.
2. **Repomix**: This code relies on `npx` or a global install of `repomix`. Ensure Node.js is available in your Linux environment.
3. **Permissions**: Ensure the script has write access to `/tmp/forge` for intermediate XML generation.
