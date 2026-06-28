"""NAD C368 Home Assistant Integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
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
)
from .helpers import merged_config
from .nad_client import NADClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.NUMBER, Platform.SWITCH, Platform.TEXT]

SERVICE_SEND_COMMAND = "send_command"
SERVICE_QUERY = "query"

SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required("command"): cv.string,
        vol.Required("value"): cv.string,
    }
)
QUERY_SCHEMA = vol.Schema({vol.Required("command"): cv.string})


def _first_client(hass: HomeAssistant):
    """Return (client, coordinator) from the first configured entry."""
    for data in hass.data.get(DOMAIN, {}).values():
        if "client" in data:
            return data["client"], data["coordinator"]
    return None, None


def _register_services(hass: HomeAssistant) -> None:
    """Register the universal send/query services once."""
    if hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        return

    async def _async_send(call: ServiceCall) -> None:
        client, coordinator = _first_client(hass)
        if client is None:
            return
        await client.send_command(call.data["command"], str(call.data["value"]))
        if coordinator is not None:
            await coordinator.async_request_refresh()

    async def _async_query(call: ServiceCall) -> dict:
        client, _ = _first_client(hass)
        if client is None:
            return {"command": call.data["command"], "value": None}
        value = await client.query(call.data["command"])
        return {"command": call.data["command"], "value": value}

    hass.services.async_register(
        DOMAIN, SERVICE_SEND_COMMAND, _async_send, schema=SEND_COMMAND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_QUERY,
        _async_query,
        schema=QUERY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAD C368 from a config entry."""
    cfg = merged_config(entry)
    host = cfg[CONF_HOST]
    port = cfg[CONF_PORT]
    poll_interval = cfg.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

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
        update_interval=timedelta(seconds=poll_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "entry": entry,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Universal "send any command" / "query any value" services.
    _register_services(hass)

    # Reload the integration when options (volume mapping) are changed.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["client"].disconnect()
        # Remove services when the last entry is gone.
        if not hass.data.get(DOMAIN):
            hass.services.async_remove(DOMAIN, SERVICE_SEND_COMMAND)
            hass.services.async_remove(DOMAIN, SERVICE_QUERY)
    return unload_ok
