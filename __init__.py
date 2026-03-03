"""LSC Smart Connect Video Doorbell - Home Assistant Integration.

Modèle testé : LSC Smart Connect Video Doorbell Rechargeable
Référence    : art. 3208999 / SI C25305
Protocole    : Tuya local (sans cloud, sans appli LSC)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import tinytuya

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
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
    DP_PRIVACY_MODE,
    EVENT_DOORBELL_PRESSED,
    EVENT_MOTION_DETECTED,
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

    # Lance la connexion persistante (push)
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


class LSCDoorbellCoordinator(DataUpdateCoordinator):
    """Coordinateur principal pour la sonnette LSC.

    Gère :
    - La connexion Tuya locale (protocole 3.3/3.4)
    - La boucle d'écoute push pour les événements (sonnette, mouvement)
    - Le polling de secours si la connexion push échoue
    """

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

    def _build_device(self) -> tinytuya.Device:
        """Construit l'objet tinytuya.Device depuis la config."""
        data = self.entry.data
        dev = tinytuya.Device(
            dev_id=data[CONF_DEVICE_ID],
            address=data[CONF_IP_ADDRESS],
            local_key=data[CONF_LOCAL_KEY],
            version=float(data.get(CONF_PROTOCOL_VERSION, "3.3")),
        )
        dev.set_socketPersistent(True)
        dev.set_socketTimeout(10)
        return dev

    async def _async_update_data(self) -> dict:
        """Polling de secours — interroge la sonnette directement."""
        try:
            result = await self.hass.async_add_executor_job(self._poll_device)
            return result
        except Exception as err:
            raise UpdateFailed(f"Erreur de communication avec la sonnette : {err}") from err

    def _poll_device(self) -> dict:
        """Synchrone — appelé dans un thread executor."""
        if self._device is None:
            self._device = self._build_device()
        status = self._device.status()
        if status and "dps" in status:
            self._last_state.update(status["dps"])
        return self._last_state.copy()

    async def async_listen_loop(self) -> None:
        """Boucle d'écoute push Tuya — tourne en arrière-plan."""
        self._running = True
        _LOGGER.info("LSC Doorbell : démarrage de la boucle d'écoute locale")

        while self._running:
            try:
                await self.hass.async_add_executor_job(self._listen_once)
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.warning("LSC Doorbell : erreur d'écoute, reconnexion dans 10s (%s)", err)
                self._device = None
                await asyncio.sleep(10)

    def _listen_once(self) -> None:
        """Bloquant — attend un message entrant de la sonnette."""
        if self._device is None:
            self._device = self._build_device()

        # Connexion et attente d'un message (timeout 35s pour rester actif)
        data = self._device.receive()
        if not data or "dps" not in data:
            return

        dps = data["dps"]
        _LOGGER.debug("LSC Doorbell reçu DPS : %s", dps)

        self._last_state.update(dps)

        # --- Événement : bouton sonnette ---
        if str(DP_DOORBELL_BUTTON) in dps or DP_DOORBELL_BUTTON in dps:
            _LOGGER.info("🔔 Sonnette appuyée !")
            self.hass.bus.fire(EVENT_DOORBELL_PRESSED, {"source": "button"})

        # --- Événement : détection de mouvement ---
        if str(DP_MOTION_DETECT) in dps or DP_MOTION_DETECT in dps:
            val = dps.get(str(DP_MOTION_DETECT), dps.get(DP_MOTION_DETECT))
            if val:
                _LOGGER.info("🚶 Mouvement détecté !")
                self.hass.bus.fire(EVENT_MOTION_DETECTED, {"source": "motion"})

        # Met à jour les entités HA
        self.async_set_updated_data(self._last_state.copy())

    async def async_shutdown(self) -> None:
        """Arrête proprement la boucle d'écoute."""
        self._running = False
        if self._device:
            await self.hass.async_add_executor_job(self._device.close)
            self._device = None
