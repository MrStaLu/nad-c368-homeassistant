"""NAD C368 Home Assistant Integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

# SupportsResponse is only available on newer Home Assistant. Import it
# defensively so the whole integration still loads on older versions.
try:
    from homeassistant.core import SupportsResponse

    _HAS_RESPONSE = True
except ImportError:  # pragma: no cover
    _HAS_RESPONSE = False

from .const import (
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    NAD_BALANCE,
    NAD_BASS,
    NAD_SPEAKER_A,
    NAD_SPEAKER_B,
    NAD_TONE_DEFEAT,
    NAD_TREBLE,
    SOURCE_NUMBERS,
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
    if _HAS_RESPONSE:
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

    # SourceN.Enabled rarely changes, so poll it only roughly every 30s (and
    # disable it automatically if the amp never answers, so it can't slow things
    # down). The per-press pull keeps the toggles fresh on user action.
    poll_state = {"enable_supported": True, "tick": 0, "enabled_cache": {}}
    enable_poll_every = max(1, round(30 / max(poll_interval, 1)))

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
                if poll_state["enable_supported"]:
                    poll_state["tick"] += 1
                    if (poll_state["tick"] - 1) % enable_poll_every == 0:
                        enabled: dict = {}
                        any_answer = False
                        for num in SOURCE_NUMBERS:
                            val = await client.get_source_enabled(num)
                            if val is not None:
                                any_answer = True
                            enabled[num] = val
                        poll_state["enabled_cache"] = enabled
                        if not any_answer:
                            # Amp doesn't expose SourceN.Enabled — stop polling.
                            poll_state["enable_supported"] = False
                    data["source_enabled"] = poll_state["enabled_cache"]
        except Exception as err:
            raise UpdateFailed(f"Error communicating with NAD C368: {err}") from err
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        config_entry=entry,
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
    """Apply option changes. Only host/port changes need a reconnect (reload);
    volume mapping, names and poll interval are applied live without the flicker
    of a full reload."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return
    client = data["client"]
    coordinator = data["coordinator"]
    cfg = merged_config(entry)

    if cfg[CONF_HOST] != client.host or cfg[CONF_PORT] != client.port:
        await hass.config_entries.async_reload(entry.entry_id)
        return

    coordinator.update_interval = timedelta(
        seconds=cfg.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    )
    coordinator.async_update_listeners()
    await coordinator.async_request_refresh()


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
