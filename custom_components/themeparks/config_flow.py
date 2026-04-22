"""Config flow for Theme Park Wait Times integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DESTINATIONS,
    DESTINATIONS_URL,
    DOMAIN,
    METHOD_GET,
    NAME,
    PARKNAME,
    PARKSLUG,
    SLUG,
    STEP_USER,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(PARKSLUG): str, vol.Required(PARKNAME): str}
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Theme Park Wait Times."""

    VERSION = 1
    _destinations: dict[str, Any] = {}

    async def _async_update_data(self):
        """Fetch list of parks."""
        client = get_async_client(self.hass)
        response = await client.request(
            METHOD_GET,
            DESTINATIONS_URL,
            timeout=10,
            follow_redirects=True,
        )
        parkdata = response.json()

        def parse_dest(item):
            slug = item[SLUG]
            name = item[NAME]
            return (name, slug)

        return dict(map(parse_dest, parkdata[DESTINATIONS]))

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Run the user config flow step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Theme Park: %s" % user_input[PARKNAME],
                data={
                    PARKSLUG: self._destinations[user_input[PARKNAME]],
                    PARKNAME: user_input[PARKNAME],
                },
            )

        if self._destinations == {}:
            self._destinations = await self._async_update_data()

        schema = {vol.Required(PARKNAME): vol.In(sorted(self._destinations.keys()))}
        return self.async_show_form(
            step_id=STEP_USER, data_schema=vol.Schema(schema), last_step=True
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Tell HA this integration supports an options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options (the 'reconfigure' screen after setup)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show the options form."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=60)
            )
        })

        return self.async_show_form(step_id="init", data_schema=schema)