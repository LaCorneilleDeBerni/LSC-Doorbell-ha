"""Select — sensibilité détection de mouvement."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DP_MOTION_SENSITIVE, MOTION_SENSITIVITY_OPTIONS
from . import LSCDoorbellCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LSCDoorbellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LSCMotionSensitivity(coordinator, entry)])


class LSCMotionSensitivity(CoordinatorEntity, SelectEntity):
    """Réglage de la sensibilité de détection de mouvement.

    Permet de choisir entre : low / medium / high
    Envoie la commande directement à la sonnette via Tuya local.

    Note : Le DP 108 est le DP supposé pour la sensibilité.
    Si ça ne fonctionne pas, utilise discover_dps.py pour trouver le bon DP.
    """

    _attr_has_entity_name = True
    _attr_name = "Sensibilité mouvement"
    _attr_icon = "mdi:motion-sensor"
    _attr_options = MOTION_SENSITIVITY_OPTIONS

    def __init__(self, coordinator: LSCDoorbellCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_motion_sensitivity"
        self._current = "medium"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="LSC Smart Connect Doorbell",
            manufacturer="Action / LSC",
            model="Video Doorbell Rechargeable (3208999)",
        )

    @property
    def current_option(self) -> str:
        data = self.coordinator.data or {}
        val = data.get(str(DP_MOTION_SENSITIVE), data.get(DP_MOTION_SENSITIVE))
        if val in MOTION_SENSITIVITY_OPTIONS:
            return val
        return self._current

    async def async_select_option(self, option: str) -> None:
        """Envoie la nouvelle sensibilité à la sonnette."""
        self._current = option
        await self.coordinator.async_set_dp(DP_MOTION_SENSITIVE, option)
        self.async_write_ha_state()
