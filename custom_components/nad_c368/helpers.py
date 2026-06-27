"""Shared config helpers for the NAD C368 integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import (
    DEFAULT_SOURCES,
    SOURCE_KEY_PREFIX,
    SOURCE_NUMBERS,
)


def merged_config(entry: ConfigEntry) -> dict:
    """Setup data with options (Configure button) layered on top."""
    return {**entry.data, **entry.options}


def get_sources(entry: ConfigEntry) -> dict[str, str]:
    """Return {source_number: display_name}, using custom names if set."""
    cfg = merged_config(entry)
    sources: dict[str, str] = {}
    for num in SOURCE_NUMBERS:
        name = cfg.get(f"{SOURCE_KEY_PREFIX}{num}")
        sources[num] = name if name else DEFAULT_SOURCES[num]
    return sources
