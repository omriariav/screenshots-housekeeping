# Test Documentation

This directory contains tests for screenshot discovery, safe file renaming, configuration, and both supported vision-model providers.

Run the complete suite from the repository root:

```bash
.venv/bin/python tests/run_tests.py
```

Provider tests mock network calls. They do not need an OpenAI API key, a running Ollama service, or a downloaded model.

## Provider and configuration coverage

- **`test_ollama_support.py`** verifies native Ollama requests and responses, model/service checks, and local error guidance.
- **`test_enhanced_error_handling.py`** verifies OpenAI and shared request-error diagnostics, retries, response parsing, and connection checks.
- **`test_desktop_path_config.py`** verifies `DESKTOP_PATH` behavior and that `OPENAI_API_KEY` is required only when `LLM_PROVIDER=openai`; Ollama mode has no key requirement.
- **`test_installation.py`** checks Python dependencies, local modules, and filesystem access. It prints the next setup steps for either provider without requiring a live provider.

Choose the provider in `.env`:

```bash
LLM_PROVIDER=openai  # Requires OPENAI_API_KEY and a vision-capable OPENAI_MODEL
# or
LLM_PROVIDER=ollama  # Requires a running Ollama service and vision-capable OLLAMA_MODEL
```

For Ollama, a typical local setup is:

```bash
ollama serve
ollama pull llama3.2-vision
```

## Screenshot and rename coverage

- **`test_grouping.py`** and **`test_rename_grouping.py`** cover timestamp grouping and applying one generated description to a group.
- **`test_regex_fix_documentation.py`**, **`test_screen_shot_support.py`**, and **`test_screen_shot_comprehensive.py`** cover modern `Screenshot` and legacy `Screen Shot` filename patterns, including single-digit hours and numbered files.
- **`test_safety_refusal_handling.py`** covers LLM refusal detection and valid-description handling.
- **`test_cost_estimation.py`** covers request/cost reporting. OpenAI estimates are approximate; Ollama's local cloud API cost is zero.

## Key behavior validated

1. Screenshot filenames and timestamp groups are identified correctly.
2. Existing files are not overwritten during rename operations.
3. Either OpenAI or Ollama can be selected explicitly with `LLM_PROVIDER`.
4. OpenAI credentials are never required for local Ollama mode.
5. A selected model must support vision/image input.
6. Provider failures are reported without preventing later files from being processed.
