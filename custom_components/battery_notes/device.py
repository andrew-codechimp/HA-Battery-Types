"""Battery Notes device, contains device level details."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.entity_registry import RegistryEntry

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN

from homeassistant.const import (
    CONF_DEVICE_ID,
    DEVICE_CLASS_BATTERY,
)

from .const import (
    PLATFORMS,
    DOMAIN,
    DOMAIN_CONFIG,
    DATA,
    DATA_STORE,
    CONF_BATTERY_TYPE,
    CONF_BATTERY_QUANTITY,
    CONF_BATTERY_LOW_THRESHOLD,
    CONF_DEFAULT_BATTERY_LOW_THRESHOLD,
    DEFAULT_BATTERY_LOW_THRESHOLD,
)

from .store import BatteryNotesStorage
from .coordinator import BatteryNotesCoordinator

_LOGGER = logging.getLogger(__name__)


class BatteryNotesDevice:
    """Manages a Battery Note device."""

    store: BatteryNotesStorage = None
    coordinator: BatteryNotesCoordinator = None
    wrapped_battery: RegistryEntry = None

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Initialize the device."""
        self.hass = hass
        self.config = config
        self.reset_jobs: list[CALLBACK_TYPE] = []

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.config.title

    @property
    def unique_id(self) -> str | None:
        """Return the unique id of the device."""
        return self.config.unique_id

    @staticmethod
    async def async_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Update the device and related entities.

        Triggered when the device is renamed on the frontend.
        """
        device_registry = dr.async_get(hass)
        # TODO: fix this
        # assert entry.unique_id
        # device_entry = device_registry.async_get_device(
        #     identifiers={(DOMAIN, entry.unique_id)}
        # )
        # assert device_entry
        # device_registry.async_update_device(device_entry.id, name=entry.title)
        await hass.config_entries.async_reload(entry.entry_id)

    async def async_setup(self) -> bool:
        """Set up the device and related entities."""
        config = self.config

        device_id = config.data.get(CONF_DEVICE_ID)

        # Find a battery for this device
        entity_registry = er.async_get(self.hass)
        for entity in entity_registry.entities.values():
            if not entity.device_id or entity.device_id != device_id:
                continue
            if not entity.domain or not entity.domain in {
                BINARY_SENSOR_DOMAIN,
                SENSOR_DOMAIN,
            }:
                continue
            if not entity.platform or entity.platform == DOMAIN:
                continue
            device_class = entity.device_class or entity.original_device_class
            if not device_class == DEVICE_CLASS_BATTERY:
                continue

            self.wrapped_battery = entity_registry.async_get(entity.entity_id)

        self.store = self.hass.data[DOMAIN][DATA_STORE]
        self.coordinator = BatteryNotesCoordinator(
            self.hass, self.store, self.wrapped_battery
        )

        self.coordinator.device_id = device_id
        self.coordinator.battery_type = config.data.get(CONF_BATTERY_TYPE)
        try:
            self.coordinator.battery_quantity = int(
                config.data.get(CONF_BATTERY_QUANTITY)
            )
        except ValueError:
            self.coordinator.battery_quantity = 1

        self.coordinator.battery_low_threshold = int(
            config.data.get(CONF_BATTERY_LOW_THRESHOLD, 0)
        )

        if self.coordinator.battery_low_threshold == 0:
            domain_config: dict = self.hass.data[DOMAIN][DOMAIN_CONFIG]
            self.coordinator.battery_low_threshold = domain_config.get(
                CONF_DEFAULT_BATTERY_LOW_THRESHOLD, DEFAULT_BATTERY_LOW_THRESHOLD
            )

        self.hass.data[DOMAIN][DATA].devices[config.entry_id] = self
        self.reset_jobs.append(config.add_update_listener(self.async_update))

        # Forward entry setup to related domains.
        await self.hass.config_entries.async_forward_entry_setups(config, PLATFORMS)

        return True

    async def async_unload(self) -> bool:
        """Unload the device and related entities."""
        if self.update_manager is None:
            return True

        while self.reset_jobs:
            self.reset_jobs.pop()()

        return await self.hass.config_entries.async_unload_platforms(
            self.config, PLATFORMS
        )
