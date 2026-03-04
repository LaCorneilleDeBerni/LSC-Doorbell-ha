"""Binary sensors — bouton sonnette et détection de mouvement."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DP_DOORBELL_BUTTON,
    DP_MOTION_DETECT,
)
from . import LSCDoorbellCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LSCDoorbellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        LSCDoorbellButtonSensor(coordinator, entry),
        LSCMotionSensor(coordinator, entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="LSC Smart Connect Doorbell",
        manufacturer="Action / LSC",
        model="Video Doorbell Rechargeable (3208999)",
    )


class LSCDoorbellButtonSensor(CoordinatorEntity, BinarySensorEntity):
    """Capteur : appui sur le bouton de la sonnette.

    Expose aussi l'URL de la photo prise lors de l'appui
    dans les attributs de l'entité.
    """

    _attr_has_entity_name = True
    _attr_name = "Bouton sonnette"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:doorbell"

    def __init__(self, coordinator: LSCDoorbellCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_doorbell_button"
        self._is_on = False
        self._last_triggered: datetime | None = None
        self._last_image_url: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry)

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "last_triggered": self._last_triggered.isoformat() if self._last_triggered else None,
            "last_image_url": self._last_image_url,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        val = data.get(str(DP_DOORBELL_BUTTON), data.get(DP_DOORBELL_BUTTON))

        if val is not None:
            # DP 212 reçoit un payload base64, pas un bool
            # On considère ON dès qu'on reçoit quelque chose
            self._is_on = True
            self._last_triggered = datetime.now()
            self._last_image_url = self.coordinator.last_image_url
            _LOGGER.info("🔔 Bouton sonnette — image : %s", self._last_image_url)

        self.async_write_ha_state()


class LSCMotionSensor(CoordinatorEntity, BinarySensorEntity):
    """Capteur : détection de mouvement."""

    _attr_has_entity_name = True
    _attr_name = "Détection de mouvement"
    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_icon = "mdi:motion-sensor"

    def __init__(self, coordinator: LSCDoorbellCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_motion"
        self._is_on = False
        self._last_triggered: datetime | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry)

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "last_triggered": self._last_triggered.isoformat() if self._last_triggered else None,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        val = data.get(str(DP_MOTION_DETECT), data.get(DP_MOTION_DETECT))

        if val is not None:
            self._is_on = bool(val)
            if self._is_on:
                self._last_triggered = datetime.now()

        self.async_write_ha_state()
