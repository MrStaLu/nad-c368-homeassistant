"""Config flow for NAD C368 integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_MAX_VOLUME,
    CONF_MIN_VOLUME,
    CONF_POLL_INTERVAL,
    CONF_VOLUME_STEP,
    DEFAULT_MAX_VOLUME,
    DEFAULT_MIN_VOLUME,
    DEFAULT_NAME,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SOURCES,
    DEFAULT_VOLUME_STEP,
    DOMAIN,
    SOURCE_KEY_PREFIX,
    SOURCE_NUMBERS,
)
from .nad_client import NADClient

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_MIN_VOLUME, default=DEFAULT_MIN_VOLUME): int,
        vol.Optional(CONF_MAX_VOLUME, default=DEFAULT_MAX_VOLUME): int,
        vol.Optional(CONF_VOLUME_STEP, default=DEFAULT_VOLUME_STEP): int,
    }
)


class NADConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NAD C368."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            # Try to connect
            client = NADClient(host, port)
            connected = await client.connect()
            await client.disconnect()

            if not connected:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "NADOptionsFlow":
        """Get the options flow for this handler."""
        return NADOptionsFlow(config_entry)


class NADOptionsFlow(config_entries.OptionsFlow):
    """Allow changing volume mapping after setup (the Configure button)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            # Drop empty source names so defaults apply
            cleaned = {k: v for k, v in user_input.items() if v != ""}
            return self.async_create_entry(title="", data=cleaned)

        # Pre-fill with current values (options override original setup data)
        current = {**self.config_entry.data, **self.config_entry.options}

        schema: dict = {
            vol.Required(
                CONF_HOST, default=current.get(CONF_HOST, "")
            ): str,
            vol.Required(
                CONF_PORT, default=current.get(CONF_PORT, DEFAULT_PORT)
            ): int,
            vol.Optional(
                CONF_POLL_INTERVAL,
                default=current.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
            ): vol.All(int, vol.Range(min=1, max=300)),
            vol.Optional(
                CONF_MIN_VOLUME,
                default=current.get(CONF_MIN_VOLUME, DEFAULT_MIN_VOLUME),
            ): vol.All(int, vol.Range(min=-90, max=20)),
            vol.Optional(
                CONF_MAX_VOLUME,
                default=current.get(CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME),
            ): vol.All(int, vol.Range(min=-90, max=20)),
            vol.Optional(
                CONF_VOLUME_STEP,
                default=current.get(CONF_VOLUME_STEP, DEFAULT_VOLUME_STEP),
            ): vol.All(int, vol.Range(min=1, max=20)),
        }

        # One text field per source so they can be renamed in the UI
        for num in SOURCE_NUMBERS:
            key = f"{SOURCE_KEY_PREFIX}{num}"
            schema[
                vol.Optional(
                    key, default=current.get(key, DEFAULT_SOURCES[num])
                )
            ] = str

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema)
        )
