import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN
from .sensor import get_containers

_LOGGER = logging.getLogger(__name__)


class WUDMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for WUD Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Förhindra duplikat av samma host+port
            await self.async_set_unique_id(f"{user_input['host']}:{user_input['port']}")
            self._abort_if_unique_id_configured()

            # Testa anslutningen innan vi sparar
            try:
                containers = await get_containers(user_input["host"], user_input["port"])
                if containers is None:
                    errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("Failed to connect to WUD: %s", e)
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=user_input["instance_name"],
                    data={
                        "host": user_input["host"],
                        "port": user_input["port"],
                        "instance_name": user_input["instance_name"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("port", default=3000): vol.All(int, vol.Range(min=1, max=65535)),
                vol.Required("instance_name"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return WUDMonitorOptionsFlowHandler()


class WUDMonitorOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    async def async_step_init(self, user_input=None):
        """Handle options."""
        errors = {}

        if user_input is not None:
            # Testa anslutningen med nya värden innan vi sparar
            try:
                containers = await get_containers(user_input["host"], user_input["port"])
                if containers is None:
                    errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("Failed to connect to WUD: %s", e)
                errors["base"] = "cannot_connect"

            if not errors:
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("host", default=self.config_entry.data.get("host", "")): str,
                vol.Optional("port", default=self.config_entry.data.get("port", 3000)): vol.All(
                    int, vol.Range(min=1, max=65535)
                ),
                vol.Optional("instance_name", default=self.config_entry.data.get("instance_name", "")): str,
            }),
            errors=errors,
        )
