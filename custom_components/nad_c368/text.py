"""NAD C368 text entities: editable input/source names.

These let the 8 source names be renamed directly from the dashboard. The value
is stored in the config entry options and reused by the media_player source list.
"""
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_NAME,
    DEFAULT_SOURCES,
    DOMAIN,
    SOURCE_KEY_PREFIX,
    SOURCE_NUMBERS,
)
from .helpers import merged_config


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(NADSourceName(entry, num) for num in SOURCE_NUMBERS)


class NADSourceName(TextEntity):
    """Editable display name for one NAD input/source."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:rename-box"
    _attr_native_min = 0
    _attr_native_max = 32

    def __init__(self, entry: ConfigEntry, num: str) -> None:
        self._entry = entry
        self._num = num
        self._key = f"{SOURCE_KEY_PREFIX}{num}"
        self._attr_name = f"Input {num} name"
        self._attr_unique_id = f"{entry.entry_id}_cfg_source_{num}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "NAD",
            "model": "C368",
        }

    @property
    def native_value(self) -> str:
        cfg = merged_config(self._entry)
        return cfg.get(self._key) or DEFAULT_SOURCES[self._num]

    async def async_set_value(self, value: str) -> None:
        new_options = {**self._entry.options, self._key: value}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
