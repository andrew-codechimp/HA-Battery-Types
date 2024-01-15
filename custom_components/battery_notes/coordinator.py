"""DataUpdateCoordinator for battery notes."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.helpers.entity_registry import RegistryEntry

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .store import BatteryNotesStorage

from .const import (
    DOMAIN,
    ATTR_REMOVE,
    LAST_REPLACED,
)

_LOGGER = logging.getLogger(__name__)


class BatteryNotesCoordinator(DataUpdateCoordinator):
    """Define an object to hold Battery Notes device."""

    device_id: str
    battery_type: str
    battery_quantity: int

    def __init__(
        self, hass, store: BatteryNotesStorage, wrapped_battery: RegistryEntry
    ):
        """Initialize."""
        self.hass = hass
        self.store = store
        self.wrapped_battery = wrapped_battery

        super().__init__(hass, _LOGGER, name=DOMAIN)

    @property
    def last_replaced(self) -> datetime:
        device_entry = self.store.async_get_device(self.device_id)
        if device_entry:
            if LAST_REPLACED in device_entry:
                last_replaced_date = datetime.fromisoformat(
                    str(device_entry[LAST_REPLACED]) + "+00:00"
                )
                return last_replaced_date
        return None

    async def _async_update_data(self):
        """Update data."""
        self.async_set_updated_data(None)

        _LOGGER.debug("Update coordinator")

    def async_update_device_config(self, device_id: str, data: dict):
        """Conditional create, update or remove device from store."""

        if ATTR_REMOVE in data:
            self.store.async_delete_device(device_id)
        elif self.store.async_get_device(device_id):
            self.store.async_update_device(device_id, data)
        else:
            self.store.async_create_device(device_id, data)

    async def async_delete_config(self):
        """Wipe battery notes storage."""

        await self.store.async_delete()
