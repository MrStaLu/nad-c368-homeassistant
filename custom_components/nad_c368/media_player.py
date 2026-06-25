"""NAD C368 media player entity."""
from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MAX_VOLUME,
    CONF_MIN_VOLUME,
    CONF_VOLUME_STEP,
    DEFAULT_MAX_VOLUME,
    DEFAULT_MIN_VOLUME,
    DEFAULT_NAME,
    DEFAULT_SOURCES,
    DEFAULT_VOLUME_STEP,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [NADMediaPlayer(data["coordinator"], data["client"], entry)]
    )


class NADMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of the NAD C368 as a media player."""

    _attr_has_entity_name = True
    _attr_name = None  # uses device name

    def __init__(self, coordinator, client, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "NAD",
            "model": "C368",
        }
        self._min_vol = entry.data.get(CONF_MIN_VOLUME, DEFAULT_MIN_VOLUME)
        self._max_vol = entry.data.get(CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME)
        self._vol_step = entry.data.get(CONF_VOLUME_STEP, DEFAULT_VOLUME_STEP)
        # Reverse map: "Optical 1" → "1"
        self._source_to_num = {v: k for k, v in DEFAULT_SOURCES.items()}

    @property
    def state(self) -> MediaPlayerState | None:
        power = self.coordinator.data.get("power")
        if power is None:
            return None
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        vol = self.coordinator.data.get("volume")
        if vol is None:
            return None
        # Convert dB (-70…0) to 0.0–1.0
        span = self._max_vol - self._min_vol
        return max(0.0, min(1.0, (vol - self._min_vol) / span))

    @property
    def is_volume_muted(self) -> bool | None:
        return self.coordinator.data.get("mute")

    @property
    def source(self) -> str | None:
        src_num = self.coordinator.data.get("source")
        return DEFAULT_SOURCES.get(src_num) if src_num else None

    @property
    def source_list(self) -> list[str]:
        return list(DEFAULT_SOURCES.values())

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        return SUPPORTED_FEATURES

    # ── Commands ──────────────────────────────────────────────────────────────

    async def async_turn_on(self) -> None:
        await self._client.set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self._client.set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self._client.set_mute(mute)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        span = self._max_vol - self._min_vol
        db = self._min_vol + (volume * span)
        await self._client.set_volume(round(db))
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        vol = self.coordinator.data.get("volume") or self._min_vol
        await self._client.set_volume(min(vol + self._vol_step, self._max_vol))
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        vol = self.coordinator.data.get("volume") or self._min_vol
        await self._client.set_volume(max(vol - self._vol_step, self._min_vol))
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        num = self._source_to_num.get(source)
        if num:
            await self._client.set_source(num)
            await self.coordinator.async_request_refresh()
