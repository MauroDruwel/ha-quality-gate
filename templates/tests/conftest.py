"""Fixtures for the {{INTEGRATION_NAME}} integration tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

# Enables custom components to be loaded in the pytest-homeassistant-custom-component harness
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Enable loading of the custom integration in every test."""
    yield
