"""NAD C368 Home Assistant Integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    NAD_BALANCE,
    NAD_BASS,
    NAD_MUTE,
    NAD_POWER,
    NAD_SOURCE,
    NAD_SPEAKER_A,
    NAD_SPEAKER_B,
    NAD_TONE_DEFEAT,
    NAD_TREBLE,
    NAD_VOLUME,
    POLL_INTERVAL,
)
from .nad_client import NADClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAD C368 from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    client = NADClient(host, port)
    if not await client.connect():
        _LOGGER.error("Cannot connect to NAD C368 at %s:%s", host, port)

    async def async_update_data() -> dict:
        """Poll all state from the amp."""
        data: dict = {}
        try:
            data["power"] = await client.get_power()
            if data["power"]:
                data["volume"] = await client.get_volume()
                data["mute"] = await client.get_mute()
                data["source"] = await client.get_source()
                data["speaker_a"] = await client.get_bool_var(NAD_SPEAKER_A)
                data["speaker_b"] = await client.get_bool_var(NAD_SPEAKER_B)
                data["tone_defeat"] = await client.get_bool_var(NAD_TONE_DEFEAT)
                data["bass"] = await client.get_int_var(NAD_BASS)
                data["treble"] = await client.get_int_var(NAD_TREBLE)
                data["balance"] = await client.get_int_var(NAD_BALANCE)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with NAD C368: {err}") from err
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=POLL_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "entry": entry,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["client"].disconnect()
    return unload_ok
