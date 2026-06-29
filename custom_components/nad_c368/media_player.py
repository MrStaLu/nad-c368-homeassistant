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
    DEFAULT_VOLUME_STEP,
    DOMAIN,
)
from .helpers import get_sources

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
        # Volume mapping and source names are read live (properties below) so the
        # Configure dialog / setting entities apply without a reload.

    # ── Live config reads (so changes apply without a reload) ──────────────────

    @property
    def _opts(self) -> dict:
        return {**self._entry.data, **self._entry.options}

    @property
    def _min_vol(self) -> int:
        return self._opts.get(CONF_MIN_VOLUME, DEFAULT_MIN_VOLUME)

    @property
    def _max_vol(self) -> int:
        return self._opts.get(CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME)

    @property
    def _vol_step(self) -> int:
        return self._opts.get(CONF_VOLUME_STEP, DEFAULT_VOLUME_STEP)

    @property
    def _sources(self) -> dict:
        return get_sources(self._entry)

    @property
    def _source_to_num(self) -> dict:
        return {v: k for k, v in self._sources.items()}

    @property
    def state(self) -> MediaPlayerState | None:
        power = (self.coordinator.data or {}).get("power")
        if power is None:
            return None
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        vol = (self.coordinator.data or {}).get("volume")
        if vol is None:
            return None
        # Convert dB (min_vol…max_vol) to 0.0–1.0
        span = self._max_vol - self._min_vol
        if span <= 0:
            return None
        return max(0.0, min(1.0, (vol - self._min_vol) / span))

    @property
    def is_volume_muted(self) -> bool | None:
        return (self.coordinator.data or {}).get("mute")

    @property
    def source(self) -> str | None:
        src_num = (self.coordinator.data or {}).get("source")
        return self._sources.get(src_num) if src_num else None

    @property
    def source_list(self) -> list[str]:
        # Only show inputs that are enabled on the amp. Unknown (None) stays
        # visible, so the list never empties if the amp doesn't report it.
        enabled = (self.coordinator.data or {}).get("source_enabled") or {}
        return [
            name
            for num, name in self._sources.items()
            if enabled.get(num) is not False
        ]

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        return SUPPORTED_FEATURES

    # ── Commands ──────────────────────────────────────────────────────────────

    def _optimistic(self, **values) -> None:
        """Update local state immediately so the UI reacts instantly."""
        if self.coordinator.data is not None:
            self.coordinator.data.update(values)
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self._client.set_power(True)
        self._optimistic(power=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self._client.set_power(False)
        self._optimistic(power=False)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self._client.set_mute(mute)
        self._optimistic(mute=mute)

    async def async_set_volume_level(self, volume: float) -> None:
        span = self._max_vol - self._min_vol
        db = round(self._min_vol + (volume * span))
        await self._client.set_volume(db)
        self._optimistic(volume=db)

    async def async_volume_up(self) -> None:
        vol = (self.coordinator.data or {}).get("volume") or self._min_vol
        new_vol = min(vol + self._vol_step, self._max_vol)
        await self._client.set_volume(new_vol)
        self._optimistic(volume=new_vol)

    async def async_volume_down(self) -> None:
        vol = (self.coordinator.data or {}).get("volume") or self._min_vol
        new_vol = max(vol - self._vol_step, self._min_vol)
        await self._client.set_volume(new_vol)
        self._optimistic(volume=new_vol)

    async def async_select_source(self, source: str) -> None:
        num = self._source_to_num.get(source)
        if num:
            await self._client.set_source(num)
            self._optimistic(source=num)
