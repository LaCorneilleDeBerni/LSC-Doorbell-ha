"""Sensor — niveau de batterie + dernière image."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DP_BATTERY
from . import LSCDoorbellCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LSCDoorbellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        LSCBatterySensor(coordinator, entry),
        LSCLastImageSensor(coordinator, entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="LSC Smart Connect Doorbell",
        manufacturer="Action / LSC",
        model="Video Doorbell Rechargeable (3208999)",
    )


class LSCBatterySensor(CoordinatorEntity, SensorEntity):
    """Capteur niveau de batterie (DP 145)."""

    _attr_has_entity_name = True
    _attr_name = "Batterie"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery"

    def __init__(self, coordinator: LSCDoorbellCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_battery"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry)

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data or {}
        val = data.get(str(DP_BATTERY), data.get(DP_BATTERY))
        return int(val) if val is not None else None


class LSCLastImageSensor(CoordinatorEntity, SensorEntity):
    """Capteur : URL de la dernière photo prise lors d'un appui."""

    _attr_has_entity_name = True
    _attr_name = "Dernière image"
    _attr_icon = "mdi:camera"

    def __init__(self, coordinator: LSCDoorbellCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_image"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.last_image_url

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "image_url": self.coordinator.last_image_url,
        }
