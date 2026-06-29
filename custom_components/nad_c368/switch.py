"""NAD C368 switch entities: Speaker A, Speaker B, Tone Defeat."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_SHOW_DB,
    DEFAULT_NAME,
    DOMAIN,
    NAD_SPEAKER_A,
    NAD_SPEAKER_B,
    NAD_TONE_DEFEAT,
    SOURCE_NUMBERS,
)


@dataclass
class NADSwitchDescription(SwitchEntityDescription):
    nad_variable: str = ""
    data_key: str = ""


SWITCH_DESCRIPTIONS: tuple[NADSwitchDescription, ...] = (
    NADSwitchDescription(
        key="speaker_a",
        name="Speaker A",
        icon="mdi:speaker",
        nad_variable=NAD_SPEAKER_A,
        data_key="speaker_a",
    ),
    NADSwitchDescription(
        key="speaker_b",
        name="Speaker B",
        icon="mdi:speaker-multiple",
        nad_variable=NAD_SPEAKER_B,
        data_key="speaker_b",
    ),
    NADSwitchDescription(
        key="tone_defeat",
        name="Tone Defeat",
        icon="mdi:music-note-off",
        nad_variable=NAD_TONE_DEFEAT,
        data_key="tone_defeat",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list = [
        NADSwitch(data["coordinator"], data["client"], entry, desc)
        for desc in SWITCH_DESCRIPTIONS
    ]
    # One power toggle per input to enable/disable the source on the amp.
    entities += [
        NADSourceEnableSwitch(data["coordinator"], data["client"], entry, num)
        for num in SOURCE_NUMBERS
    ]
    # Dashboard display toggle: show volume in dB instead of %.
    entities.append(NADShowDbSwitch(entry))
    async_add_entities(entities)


class NADSwitch(CoordinatorEntity, SwitchEntity):
    """A toggle switch for NAD C368 speaker and tone controls."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, client, entry: ConfigEntry, desc: NADSwitchDescription) -> None:
        super().__init__(coordinator)
        self._client = client
        self._desc = desc
        self.entity_description = desc
        self._attr_unique_id = f"{entry.entry_id}_{desc.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "NAD",
            "model": "C368",
        }

    @property
    def is_on(self) -> bool | None:
        return (self.coordinator.data or {}).get(self._desc.data_key)

    def _optimistic(self, value: bool) -> None:
        if self.coordinator.data is not None:
            self.coordinator.data[self._desc.data_key] = value
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        await self._client.set_bool_var(self._desc.nad_variable, True)
        self._optimistic(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.set_bool_var(self._desc.nad_variable, False)
        self._optimistic(False)


class NADSourceEnableSwitch(CoordinatorEntity, SwitchEntity):
    """Power toggle that enables/disables one input (SourceN.Enabled) on the amp."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:power"

    def __init__(self, coordinator, client, entry: ConfigEntry, num: str) -> None:
        super().__init__(coordinator)
        self._client = client
        self._num = num
        self._attr_name = f"Input {num} enabled"
        self._attr_unique_id = f"{entry.entry_id}_source_{num}_enabled"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "NAD",
            "model": "C368",
        }

    @property
    def is_on(self) -> bool | None:
        return ((self.coordinator.data or {}).get("source_enabled") or {}).get(self._num)

    async def _pull_status(self) -> None:
        """Query the amp for the real state, then refresh this + the source list."""
        value = await self._client.get_source_enabled(self._num)
        if self.coordinator.data is not None:
            self.coordinator.data.setdefault("source_enabled", {})[self._num] = value
        self.coordinator.async_update_listeners()

    async def async_turn_on(self, **kwargs) -> None:
        await self._client.set_source_enabled(self._num, True)
        await self._pull_status()

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.set_source_enabled(self._num, False)
        await self._pull_status()


class NADShowDbSwitch(SwitchEntity):
    """Dashboard display toggle: show the volume in dB instead of %.

    Stored in the config entry options; flipping it applies live (no reload).
    A conditional card on the dashboard reacts to this switch's state.
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:swap-horizontal"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_name = "Volume in dB"
        self._attr_unique_id = f"{entry.entry_id}_show_db"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "NAD",
            "model": "C368",
        }

    @property
    def is_on(self) -> bool:
        return bool({**self._entry.data, **self._entry.options}.get(CONF_SHOW_DB, False))

    def _set(self, value: bool) -> None:
        self.hass.config_entries.async_update_entry(
            self._entry, options={**self._entry.options, CONF_SHOW_DB: value}
        )

    async def async_turn_on(self, **kwargs) -> None:
        self._set(True)

    async def async_turn_off(self, **kwargs) -> None:
        self._set(False)
