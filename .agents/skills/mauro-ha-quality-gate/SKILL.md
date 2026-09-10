---
name: mauro-ha-quality-gate
description: Standards, rules, workflows, and quality gate guidelines for Home Assistant integrations authored by Mauro Druwel. Load when creating, reviewing, refactoring, or auditing any Home Assistant custom component integration.
---

# Mauro Quality Gate (MQG) for Home Assistant

This skill governs the standards, architecture, testing, and CI/CD pipelines for all Home Assistant custom components maintained by **Mauro Druwel** (@MauroDruwel).

The authoritative central repository, templates, and automated auditing script are hosted at:
👉 **`https://github.com/MauroDruwel/ha-quality-gate`**

---

## 1. GitHub Repository Topics & Metadata

Do not overload repositories with excessive tags. Use strictly:

| Topic | Rule | Command |
|---|---|---|
| `home-assistant-integration` | **Mandatory** on all custom component integrations | `gh repo edit MauroDruwel/<repo> --add-topic home-assistant-integration` |
| `hacs` | **Only** when accepted in official `hacs/default` | `gh repo edit MauroDruwel/<repo> --add-topic hacs` |

---

## 2. Directory Layout & Architecture

Every integration MUST conform to this standard directory structure:

```text
custom_components/<domain>/
├── brand/
│   ├── icon.png          # 256x256 square brand icon
│   ├── icon@2x.png       # 512x512 square brand icon
│   ├── logo.png          # Wide brand logo
│   └── logo@2x.png       # High-res wide brand logo
├── __init__.py           # async_setup_entry, async_unload_entry, coordinator setup
├── config_flow.py        # ConfigFlow and OptionsFlow (with translations)
├── const.py              # DOMAIN, defaults, intervals, thresholds
├── coordinator.py        # DataUpdateCoordinator with auth recovery & retry
├── manifest.json         # Integration manifest
├── strings.json          # Source strings
├── translations/
│   ├── en.json           # English translations
│   └── nl.json           # Dutch translations (always provide both!)
├── sensor.py             # Platforms (sensor, binary_sensor, etc.)
└── py.typed              # Typing marker

.github/workflows/
├── validate.yml          # Hassfest & HACS action validation
└── tests.yml             # Pytest in CI

tests/
├── conftest.py           # auto_enable_custom_integrations fixture + client mocks
├── test_config_flow.py   # Full coverage of setup & options flow
└── test_init.py          # Entry setup, unload, API retry, entity attributes

hacs.json                 # {"name": "...", "render_readme": true}
pytest.ini                # testpaths = tests, pythonpath = ., asyncio_mode = auto
README.md                 # Badges, features, HACS install guide, debug logging
```

---

## 3. Manifest & HACS Rules

### `manifest.json` Requirements
- `"codeowners"`: Must include `["@MauroDruwel"]`
- `"integration_type"`: `"device"` (or `"service"`, `"hub"`)
- `"iot_class"`: `"cloud_polling"`, `"cloud_push"`, `"local_polling"`, or `"local_push"`
- `"config_flow"`: `true` (every integration must support UI configuration)
- `"version"`: SemVer (e.g. `"1.1.0"`) matching git release tags
- `"issue_tracker"`: URL to repo issues
- `"requirements"`: Clean dependency pins/bounds (e.g. `weathercloud>=0.1.5`)

### `hacs.json` Requirements
```json
{
  "name": "Integration Name",
  "render_readme": true
}
```

---

## 4. Standard CI/CD Pipelines

All integrations must have these two workflows in `.github/workflows/`:

### `.github/workflows/validate.yml`
```yaml
name: Validate

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 4 * * 1"
  workflow_dispatch:

jobs:
  hassfest:
    name: Hassfest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: home-assistant/actions/hassfest@master

  hacs:
    name: HACS
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: hacs/action@main
        with:
          category: integration
```

### `.github/workflows/tests.yml`
```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  pytest:
    name: pytest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest-homeassistant-custom-component pytest-asyncio pytest-cov
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: Run tests
        run: pytest
```

---

## 5. Testing & Verification Standards

1. Use `pytest-homeassistant-custom-component`.
2. In `pytest.ini`, ensure `pythonpath = .` is set.
3. In `tests/conftest.py`, ensure `auto_enable_custom_integrations` is active and `MockConfigEntry` sets `version` matching `ConfigFlow.VERSION`.
4. Test Coverage checklist:
   - Setup & unload lifecycle (`ConfigEntryState.LOADED` -> `NOT_LOADED`).
   - Clean session teardown on unload (`client.close()` called).
   - `ConfigEntryNotReady` on transient API failure.
   - Config flow: valid credentials, invalid credentials, duplicate instance abort.
   - Options flow (if configurable polling interval or toggles exist).
   - Entity attributes (including `ATTR_LATITUDE` and `ATTR_LONGITUDE` for map cards).

---

## 6. Audit & Validation Tool

To check any integration against these rules:

```bash
python /path/to/ha-quality-gate/scripts/audit_integration.py /path/to/integration
python /path/to/ha-quality-gate/scripts/audit_integration.py MauroDruwel/SMA-ennexOS-cloud-HA --remote
```
