"""LSC Smart Connect Video Doorbell - Home Assistant Integration."""

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
    DOMAIN, PLATFORMS, CONF_DEVICE_ID, CONF_LOCAL_KEY, CONF_IP_ADDRESS,
    CONF_PROTOCOL_VERSION, POLLING_INTERVAL, DP_DOORBELL_BUTTON,
    DP_MOTION_DETECT, EVENT_DOORBELL_PRESSED, EVENT_MOTION_DETECTED,
    DEFAULT_PROTOCOL_VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = LSCDoorbellCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    asyncio.ensure_future(coordinator.async_listen_loop())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok


def _decode_doorbell_payload(raw_value) -> dict:
    try:
        if isinstance(raw_value, str):
            decoded = base64.b64decode(raw_value + "==").decode("utf-8")
            data = json.loads(decoded)
            image_url = None
            if "files" in data and data["files"]:
                f = data["files"][0]
                if len(f) >= 2:
                    image_url = f"https://{f[0]}.oss-eu-central-1.aliyuncs.com{f[1]}"
            return {
                "cmd": data.get("cmd", ""),
                "alarm": data.get("alarm", False),
                "time": data.get("time", 0),
                "image_url": image_url,
            }
    except Exception as err:
        _LOGGER.debug("Impossible de decoder DP212 : %s", err)
    return {}


class LSCDoorbellCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
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
        )
        dev.set_version(float(data.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION)))
        dev.set_socketPersistent(True)
        dev.set_socketTimeout(30)
        return dev

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._poll_device)
        except Exception as err:
            raise UpdateFailed(f"Erreur : {err}") from err

    def _poll_device(self) -> dict:
        if self._device is None:
            self._device = self._build_device()
        status = self._device.status()
        if status and "dps" in status:
            self._last_state.update(status["dps"])
        return self._last_state.copy()

    async def async_listen_loop(self) -> None:
        self._running = True
        _LOGGER.info("LSC Doorbell : boucle d'ecoute demarree")
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
        _LOGGER.info("LSC Doorbell DPS recus : %s", dps)
        self._last_state.update(dps)

        dp212 = dps.get("212", dps.get(212))
        if dp212 is not None:
            payload = _decode_doorbell_payload(dp212)
            if payload.get("cmd") in ("ipc_doorbell", "ipc_human"):
                self.last_image_url = payload.get("image_url")
                _LOGGER.info("Sonnette ! image=%s", self.last_image_url)
                self.hass.loop.call_soon_threadsafe(
                    self.hass.bus.fire, EVENT_DOORBELL_PRESSED, {
                        "image_url": self.last_image_url,
                        "time": payload.get("time"),
                    }
                )

        dp149 = dps.get("149", dps.get(149))
        if dp149:
            _LOGGER.info("Mouvement detecte !")
            self.hass.loop.call_soon_threadsafe(
                self.hass.bus.fire, EVENT_MOTION_DETECTED, {}
            )

        self.hass.loop.call_soon_threadsafe(
            self.async_set_updated_data, self._last_state.copy()
        )

    async def async_set_dp(self, dp: int, value) -> None:
        await self.hass.async_add_executor_job(self._set_dp_sync, dp, value)

    def _set_dp_sync(self, dp: int, value) -> None:
        if self._device is None:
            self._device = self._build_device()
        self._device.set_value(dp, value)

    async def async_shutdown(self) -> None:
        self._running = False
        if self._device:
            try:
                await self.hass.async_add_executor_job(self._device.close)
            except Exception:
                pass
        self._device = None
