"""Entité caméra — flux RTSP + audio de la sonnette LSC."""

from __future__ import annotations

import logging

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_IP_ADDRESS,
    CONF_RTSP_PORT,
    CONF_RTSP_PATH,
    DEFAULT_RTSP_PORT,
    DEFAULT_RTSP_PATH,
)
from . import LSCDoorbellCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure la plateforme caméra."""
    coordinator: LSCDoorbellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LSCDoorbellCamera(coordinator, entry)])


class LSCDoorbellCamera(CoordinatorEntity, Camera):
    """Caméra LSC — flux RTSP vidéo + audio en local.

    Le flux RTSP est fourni directement par la caméra sans passer
    par le cloud Tuya. L'audio (microphone) est inclus dans le flux
    si la sonnette l'expose sur le stream RTSP.

    URL du flux : rtsp://<IP>:<PORT><PATH>
    Exemple     : rtsp://192.168.1.50:554/stream0
    """

    _attr_has_entity_name = True
    _attr_name = "Caméra"
    _attr_icon = "mdi:doorbell-video"
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(
        self,
        coordinator: LSCDoorbellCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        Camera.__init__(self)

        self._entry = entry
        ip = entry.data[CONF_IP_ADDRESS]
        port = entry.data.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT)
        path = entry.data.get(CONF_RTSP_PATH, DEFAULT_RTSP_PATH)

        self._rtsp_url = f"rtsp://{ip}:{port}{path}"
        self._attr_unique_id = f"{entry.entry_id}_camera"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="LSC Smart Connect Doorbell",
            manufacturer="Action / LSC",
            model="Video Doorbell Rechargeable (3208999)",
        )

    async def stream_source(self) -> str | None:
        """Retourne l'URL RTSP du flux vidéo/audio."""
        return self._rtsp_url

    @property
    def is_streaming(self) -> bool:
        """La caméra est considérée en streaming si le coordinateur est actif."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "rtsp_url": self._rtsp_url,
            "model": "LSC 3208999",
        }
