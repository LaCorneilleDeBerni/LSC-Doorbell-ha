"""Config Flow — LSC Smart Connect Video Doorbell."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_IP_ADDRESS,
    CONF_PROTOCOL_VERSION,
    CONF_RTSP_PORT,
    CONF_RTSP_PATH,
    DEFAULT_PROTOCOL_VERSION,
    DEFAULT_RTSP_PORT,
    DEFAULT_RTSP_PATH,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS, description={"suggested_value": "192.168.1.218"}): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_LOCAL_KEY): str,
        vol.Optional(CONF_PROTOCOL_VERSION, default=DEFAULT_PROTOCOL_VERSION): vol.In(
            ["3.1", "3.2", "3.3", "3.4", "3.5"]
        ),
        vol.Optional(CONF_RTSP_PORT, default=DEFAULT_RTSP_PORT): int,
        vol.Optional(CONF_RTSP_PATH, default=DEFAULT_RTSP_PATH): str,
    }
)


class LSCDoorbellConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère la configuration via l'UI de Home Assistant."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            # On ne teste plus la connexion ici car la sonnette
            # (protocole 3.5, haute latence) peut refuser le test rapide.
            # La connexion réelle se fait dans le coordinateur au démarrage.
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"LSC Doorbell ({user_input[CONF_IP_ADDRESS]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
