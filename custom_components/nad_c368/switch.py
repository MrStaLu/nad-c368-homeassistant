"""NAD C368 switch entities: Speaker A, Speaker B, Tone Defeat."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN, NAD_SPEAKER_A, NAD_SPEAKER_B, NAD_TONE_DEFEAT


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
    async_add_entities(
        NADSwitch(data["coordinator"], data["client"], entry, desc)
        for desc in SWITCH_DESCRIPTIONS
    )


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
        return self.coordinator.data.get(self._desc.data_key)

    async def async_turn_on(self, **kwargs) -> None:
        await self._client.set_bool_var(self._desc.nad_variable, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.set_bool_var(self._desc.nad_variable, False)
        await self.coordinator.async_request_refresh()
