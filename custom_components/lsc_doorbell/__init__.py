"""LSC Smart Connect Video Doorbell - Home Assistant Integration.

Modèle testé : LSC Smart Connect Video Doorbell Rechargeable
Référence    : art. 3208999 / SI C25305
Protocole    : Tuya local v3.5 (sans cloud, sans appli LSC)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from datetime import timedelta

import tinytuya

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_IP_ADDRESS,
    CONF_PROTOCOL_VERSION,
    POLLING_INTERVAL,
    DP_DOORBELL_BUTTON,
    DP_MOTION_DETECT,
    DP_BATTERY,
    EVENT_DOORBELL_PRESSED,
    EVENT_MOTION_DETECTED,
    DEFAULT_PROTOCOL_VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialise l'intégration depuis une config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = LSCDoorbellCoordinator(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(
        hass.async_create_background_task(
            coordinator.async_listen_loop(),
            name="lsc_doorbell_listen",
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok


def _decode_doorbell_payload(raw_value) -> dict:
    """Décode le payload base64 du DP 212 (bouton sonnette + photo)."""
    try:
        if isinstance(raw_value, str):
            decoded = base64.b64decode(raw_value + "==").decode("utf-8")
            data = json.loads(decoded)
            # Extraire l'URL de l'image depuis le tableau files
            image_url = None
            if "files" in data and data["files"]:
                file_entry = data["files"][0]
                if len(file_entry) >= 2:
                    bucket = file_entry[0]
                    path = file_entry[1]
                    image_url = f"https://{bucket}.oss-eu-central-1.aliyuncs.com{path}"
            return {
                "cmd": data.get("cmd", ""),
                "alarm": data.get("alarm", False),
                "time": data.get("time", 0),
                "image_url": image_url,
            }
    except Exception as err:
        _LOGGER.debug("Impossible de décoder le payload DP212 : %s", err)
    return {}


class LSCDoorbellCoordinator(DataUpdateCoordinator):
    """Coordinateur principal pour la sonnette LSC."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLLING_INTERVAL),
        )
        self.entry = entry
        self._device: tinytuya.Device | None = None
        self._running = False
        self._last_state: dict = {}
        self.last_image_url: str | None = None

    def _build_device(self) -> tinytuya.Device:
        data = self.entry.data
        dev = tinytuya.Device(
            dev_id=data[CONF_DEVICE_ID],
            address=data[CONF_IP_ADDRESS],
            local_key=data[CONF_LOCAL_KEY],
            version=float(data.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION)),
        )
        dev.set_socketPersistent(True)
        dev.set_socketTimeout(30)
        return dev

    async def _async_update_data(self) -> dict:
        try:
            result = await self.hass.async_add_executor_job(self._poll_device)
            return result
        except Exception as err:
            raise UpdateFailed(f"Erreur de communication : {err}") from err

    def _poll_device(self) -> dict:
        if self._device is None:
            self._device = self._build_device()
        status = self._device.status()
        if status and "dps" in status:
            self._last_state.update(status["dps"])
        return self._last_state.copy()

    async def async_listen_loop(self) -> None:
        """Boucle d'écoute push — tourne en arrière-plan."""
        self._running = True
        _LOGGER.info("LSC Doorbell : démarrage de la boucle d'écoute")

        while self._running:
            try:
                await self.hass.async_add_executor_job(self._listen_once)
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.warning("LSC Doorbell : erreur, reconnexion dans 10s (%s)", err)
                self._device = None
                await asyncio.sleep(10)

    def _listen_once(self) -> None:
        if self._device is None:
            self._device = self._build_device()

        data = self._device.receive()
        if not data or "dps" not in data:
            return

        dps = data["dps"]
        _LOGGER.debug("LSC Doorbell DPS reçus : %s", dps)
        self._last_state.update(dps)

        # --- Bouton sonnette (DP 212) ---
        dp212 = dps.get(str(DP_DOORBELL_BUTTON), dps.get(DP_DOORBELL_BUTTON))
        if dp212 is not None:
            payload = _decode_doorbell_payload(dp212)
            if payload.get("cmd") == "ipc_doorbell":
                self.last_image_url = payload.get("image_url")
                _LOGGER.info("🔔 Sonnette ! Image : %s", self.last_image_url)
                self.hass.bus.fire(EVENT_DOORBELL_PRESSED, {
                    "image_url": self.last_image_url,
                    "time": payload.get("time"),
                })

        # --- Détection mouvement (DP 149) ---
        dp149 = dps.get(str(DP_MOTION_DETECT), dps.get(DP_MOTION_DETECT))
        if dp149:
            _LOGGER.info("🚶 Mouvement détecté !")
            self.hass.bus.fire(EVENT_MOTION_DETECTED, {})

        self.async_set_updated_data(self._last_state.copy())

    async def async_set_dp(self, dp: int, value) -> None:
        """Envoie une commande à la sonnette (ex: sensibilité mouvement)."""
        await self.hass.async_add_executor_job(self._set_dp_sync, dp, value)

    def _set_dp_sync(self, dp: int, value) -> None:
        if self._device is None:
            self._device = self._build_device()
        self._device.set_value(dp, value)
        _LOGGER.info("LSC Doorbell : DP %s = %s", dp, value)

    async def async_shutdown(self) -> None:
        self._running = False
        if self._device:
            await self.hass.async_add_executor_job(self._device.close)
            self._device = None
