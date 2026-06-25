"""NAD C368 number entities: Bass, Treble, Balance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN, NAD_BALANCE, NAD_BASS, NAD_TREBLE


@dataclass
class NADNumberDescription(NumberEntityDescription):
    nad_variable: str = ""
    data_key: str = ""


NUMBER_DESCRIPTIONS: tuple[NADNumberDescription, ...] = (
    NADNumberDescription(
        key="bass",
        name="Bass",
        icon="mdi:equalizer",
        native_min_value=-7,
        native_max_value=7,
        native_step=1,
        native_unit_of_measurement="dB",
        nad_variable=NAD_BASS,
        data_key="bass",
    ),
    NADNumberDescription(
        key="treble",
        name="Treble",
        icon="mdi:equalizer-outline",
        native_min_value=-7,
        native_max_value=7,
        native_step=1,
        native_unit_of_measurement="dB",
        nad_variable=NAD_TREBLE,
        data_key="treble",
    ),
    NADNumberDescription(
        key="balance",
        name="Balance",
        icon="mdi:scale-balance",
        native_min_value=-18,
        native_max_value=18,
        native_step=1,
        nad_variable=NAD_BALANCE,
        data_key="balance",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NADNumber(data["coordinator"], data["client"], entry, desc)
        for desc in NUMBER_DESCRIPTIONS
    )


class NADNumber(CoordinatorEntity, NumberEntity):
    """A slider entity for NAD C368 tone controls."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, client, entry: ConfigEntry, desc: NADNumberDescription) -> None:
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
    def native_value(self) -> float | None:
        val = self.coordinator.data.get(self._desc.data_key)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self._client.set_int_var(self._desc.nad_variable, int(value))
        await self.coordinator.async_request_refresh()
