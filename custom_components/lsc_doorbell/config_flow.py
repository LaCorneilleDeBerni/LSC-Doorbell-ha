"""Config Flow — LSC Smart Connect Video Doorbell."""

from __future__ import annotations

import logging
from typing import Any

import tinytuya
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
        vol.Required(CONF_IP_ADDRESS, description={"suggested_value": "192.168.1.XX"}): str,
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
        """Étape principale : saisie des paramètres de connexion."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Teste la connexion à la sonnette
            error = await self.hass.async_add_executor_job(
                self._test_connection,
                user_input[CONF_IP_ADDRESS],
                user_input[CONF_DEVICE_ID],
                user_input[CONF_LOCAL_KEY],
                user_input.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION),
            )

            if error is None:
                # Connexion OK → crée l'entrée
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"LSC Doorbell ({user_input[CONF_IP_ADDRESS]})",
                    data=user_input,
                )
            else:
                errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "help": "Entrez l'IP, Device ID et Local Key récupérés avec tinytuya wizard"
            },
        )

    def _test_connection(
        self, ip: str, device_id: str, local_key: str, version: str
    ) -> str | None:
        """Teste la connexion Tuya locale. Retourne None si OK, sinon un code d'erreur."""
        try:
            dev = tinytuya.Device(
                dev_id=device_id,
                address=ip,
                local_key=local_key,
                version=float(version),
            )
            dev.set_socketTimeout(8)
            result = dev.status()
            dev.close()

            if result is None:
                return "cannot_connect"
            if "Error" in str(result):
                _LOGGER.error("Erreur connexion LSC : %s", result)
                return "invalid_auth"
            return None

        except ConnectionRefusedError:
            return "cannot_connect"
        except Exception as err:
            _LOGGER.exception("Erreur inattendue lors du test connexion : %s", err)
            return "unknown"
