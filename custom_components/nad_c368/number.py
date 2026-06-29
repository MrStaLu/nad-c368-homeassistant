"""NAD C368 number entities: Bass, Treble, Balance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MAX_VOLUME,
    CONF_MIN_VOLUME,
    CONF_POLL_INTERVAL,
    CONF_VOLUME_STEP,
    DEFAULT_MAX_VOLUME,
    DEFAULT_MIN_VOLUME,
    DEFAULT_NAME,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_VOLUME_STEP,
    DOMAIN,
    NAD_BALANCE,
    NAD_BASS,
    NAD_TREBLE,
)
from .helpers import merged_config


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
    entities: list = [
        NADNumber(data["coordinator"], data["client"], entry, desc)
        for desc in NUMBER_DESCRIPTIONS
    ]
    # Configuration numbers — edit the volume mapping / polling from the dashboard.
    entities += [
        NADConfigNumber(entry, CONF_MIN_VOLUME, "Minimum volume",
                        -90, 20, 1, DEFAULT_MIN_VOLUME, "dB", "mdi:volume-low"),
        NADConfigNumber(entry, CONF_MAX_VOLUME, "Maximum volume",
                        -90, 20, 1, DEFAULT_MAX_VOLUME, "dB", "mdi:volume-high"),
        NADConfigNumber(entry, CONF_VOLUME_STEP, "Volume step",
                        1, 20, 1, DEFAULT_VOLUME_STEP, "dB", "mdi:plus-minus-variant"),
        NADConfigNumber(entry, CONF_POLL_INTERVAL, "Poll interval",
                        1, 300, 1, DEFAULT_POLL_INTERVAL, "s", "mdi:timer-sync"),
    ]
    # Two views of the same volume — % and dB — sharing the same min→max mapping.
    entities += [
        NADVolumeNumber(data["coordinator"], data["client"], entry, "percent"),
        NADVolumeNumber(data["coordinator"], data["client"], entry, "db"),
    ]
    async_add_entities(entities)


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
        val = (self.coordinator.data or {}).get(self._desc.data_key)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self._client.set_int_var(self._desc.nad_variable, int(value))
        if self.coordinator.data is not None:
            self.coordinator.data[self._desc.data_key] = int(value)
        self.async_write_ha_state()


class NADConfigNumber(NumberEntity):
    """A configuration number stored in the config entry options.

    Lets the volume mapping and poll interval be edited directly from the
    dashboard. Changing it updates the entry options and reloads the integration.
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: ConfigEntry, key: str, name: str, mn: int, mx: int,
                 step: int, default: int, unit: str, icon: str) -> None:
        self._entry = entry
        self._key = key
        self._default = default
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_min_value = mn
        self._attr_native_max_value = mx
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_cfg_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "NAD",
            "model": "C368",
        }

    @property
    def native_value(self) -> float | None:
        return merged_config(self._entry).get(self._key, self._default)

    async def async_set_native_value(self, value: float) -> None:
        new_options = {**self._entry.options, self._key: int(value)}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)


class NADVolumeNumber(CoordinatorEntity, NumberEntity):
    """The current volume shown as % or dB. Both views share the same min→max
    mapping, so 0 % == Min volume and 100 % == Max volume in either view."""

    _attr_has_entity_name = True
    _attr_native_step = 1

    def __init__(self, coordinator, client, entry: ConfigEntry, mode: str) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._mode = mode  # "percent" or "db"
        if mode == "percent":
            self._attr_name = "Volume percent"
            self._attr_native_unit_of_measurement = "%"
            self._attr_icon = "mdi:volume-high"
        else:
            self._attr_name = "Volume dB"
            self._attr_native_unit_of_measurement = "dB"
            self._attr_icon = "mdi:sine-wave"
        self._attr_unique_id = f"{entry.entry_id}_volume_{mode}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "NAD",
            "model": "C368",
        }

    @property
    def _min_vol(self) -> int:
        return merged_config(self._entry).get(CONF_MIN_VOLUME, DEFAULT_MIN_VOLUME)

    @property
    def _max_vol(self) -> int:
        return merged_config(self._entry).get(CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME)

    @property
    def native_min_value(self) -> float:
        return 0 if self._mode == "percent" else self._min_vol

    @property
    def native_max_value(self) -> float:
        return 100 if self._mode == "percent" else self._max_vol

    @property
    def native_value(self) -> float | None:
        vol = (self.coordinator.data or {}).get("volume")
        if vol is None:
            return None
        if self._mode == "db":
            return float(vol)
        span = self._max_vol - self._min_vol
        if span <= 0:
            return None
        return round(max(0.0, min(100.0, (vol - self._min_vol) / span * 100)))

    async def async_set_native_value(self, value: float) -> None:
        if self._mode == "db":
            db = round(value)
        else:
            span = self._max_vol - self._min_vol
            db = round(self._min_vol + (value / 100) * span)
        await self._client.set_volume(db)
        if self.coordinator.data is not None:
            self.coordinator.data["volume"] = db
        self.async_write_ha_state()
        # Keep the media player and the other (%/dB) view in sync immediately.
        self.coordinator.async_update_listeners()
