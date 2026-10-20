"""Config flow for EZR XML."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers import selector

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


class EzrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            scan_interval = user_input["scan_interval"]

            # Basis-URL akzeptieren und den XML-Pfad automatisch ergänzen.
            if url.endswith("/data/static.xml"):
                base_url = url.removesuffix("/data/static.xml")
            else:
                base_url = url

            url = f"{base_url}/data/static.xml"

            try:
                from .coordinator import EzrCoordinator

                test_coordinator = EzrCoordinator(
                    self.hass, url, scan_interval
                )
                await test_coordinator.async_refresh()

                if test_coordinator.last_update_success is False:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(url)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="EZR XML",
                        data={
                            CONF_URL: url,
                            "scan_interval": scan_interval,
                        },
                    )
            except Exception:
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_URL): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
                vol.Required(
                    "scan_interval",
                    default=DEFAULT_SCAN_INTERVAL,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=10, max=3600),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "url_example": "http://192.168.1.100",
            },
        )