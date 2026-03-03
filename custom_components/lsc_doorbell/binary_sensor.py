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
    EVENT_DOORBELL_PRESSED,
    EVENT_MOTION_DETECTED,
)
from . import LSCDoorbellCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les binary sensors."""
    coordinator: LSCDoorbellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        LSCDoorbellButtonSensor(coordinator, entry),
        LSCMotionSensor(coordinator, entry),
    ])


class LSCDoorbellButtonSensor(CoordinatorEntity, BinarySensorEntity):
    """Capteur : appui sur le bouton de la sonnette.

    Passe à ON brièvement lors d'un appui, puis revient à OFF.
    Déclenche aussi l'événement lsc_doorbell_button_pressed dans HA.
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

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="LSC Smart Connect Doorbell",
            manufacturer="Action / LSC",
            model="Video Doorbell Rechargeable (3208999)",
        )

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
        """Réagit aux mises à jour des DPS Tuya."""
        data = self.coordinator.data or {}
        val = data.get(str(DP_DOORBELL_BUTTON), data.get(DP_DOORBELL_BUTTON))

        if val is not None:
            self._is_on = bool(val)
            if self._is_on:
                self._last_triggered = datetime.now()
                _LOGGER.info("🔔 Bouton sonnette activé")

        self.async_write_ha_state()


class LSCMotionSensor(CoordinatorEntity, BinarySensorEntity):
    """Capteur : détection de mouvement par la sonnette.

    Passe à ON quand la sonnette détecte un mouvement.
    Déclenche aussi l'événement lsc_doorbell_motion_detected dans HA.
    """

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
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="LSC Smart Connect Doorbell",
            manufacturer="Action / LSC",
            model="Video Doorbell Rechargeable (3208999)",
        )

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
                _LOGGER.info("🚶 Mouvement détecté")

        self.async_write_ha_state()
