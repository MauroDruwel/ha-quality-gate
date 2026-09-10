# {{INTEGRATION_NAME}} for Home Assistant

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/MauroDruwel/{{REPO_NAME}}?style=flat-square)](https://github.com/MauroDruwel/{{REPO_NAME}}/releases)
[![Validate](https://github.com/MauroDruwel/{{REPO_NAME}}/actions/workflows/validate.yml/badge.svg)](https://github.com/MauroDruwel/{{REPO_NAME}}/actions/workflows/validate.yml)
[![Tests](https://github.com/MauroDruwel/{{REPO_NAME}}/actions/workflows/tests.yml/badge.svg)](https://github.com/MauroDruwel/{{REPO_NAME}}/actions/workflows/tests.yml)
[![License](https://img.shields.io/github/license/MauroDruwel/{{REPO_NAME}}?style=flat-square)](LICENSE)

{{SHORT_DESCRIPTION}}

---

## Features

- ⚡ **Full UI Configuration** via Home Assistant Config Flow (no YAML required).
- 🔄 **Options Flow**: Configure polling intervals and options dynamically.
- 🌍 **Map Visualization**: Sensor GPS coordinates (`latitude`/`longitude`) populated automatically for map cards.
- 🛡️ **Session Recovery**: Automated re-authentication and exponential retry handling.
- 🌐 **Multilingual**: English and Dutch (`en.json` / `nl.json`) translations.

---

## Installation

### Method 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. In HACS, go to **Integrations** > click the three dots in top right > **Custom repositories**.
3. Add `https://github.com/MauroDruwel/{{REPO_NAME}}` with category **Integration**.
4. Search for **{{INTEGRATION_NAME}}**, click **Download**, and restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/MauroDruwel/{{REPO_NAME}}/releases) page.
2. Copy the `custom_components/{{DOMAIN}}` directory to your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for **{{INTEGRATION_NAME}}**.
3. Enter your credentials and complete the setup.

---

## Debug Logging

If you encounter issues, enable debug logging in your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.{{DOMAIN}}: debug
```

---

## Author & License

Developed by **Mauro Druwel** ([@MauroDruwel](https://github.com/MauroDruwel)) — [maurodruwel.be](https://maurodruwel.be).

Licensed under the MIT License.
