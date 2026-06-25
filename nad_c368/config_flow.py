"""Config flow for NAD C368 integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_MAX_VOLUME,
    CONF_MIN_VOLUME,
    CONF_VOLUME_STEP,
    DEFAULT_MAX_VOLUME,
    DEFAULT_MIN_VOLUME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_VOLUME_STEP,
    DOMAIN,
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
