import logging
import aiohttp
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
DOMAIN = "wud_getupdates"

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up the WUD sensor platform."""
    wud_host = config_entry.data["host"]
    wud_port = config_entry.data["port"]
    instance_name = config_entry.data["instance_name"]

    containers = await get_containers(wud_host, wud_port)

    sensors = []
    for container in containers:
        sensors.append(WUDContainerSensor(container, config_entry, instance_name))

    async_add_entities(sensors, True)


async def get_containers(host, port):
    """Fetch containers from the WUD API."""
    url = f"http://{host}:{port}/api/containers"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # API returnerar antingen en lista eller ett dict med "items"
                if isinstance(data, list):
                    return data
                return data.get("items", [])
            else:
                _LOGGER.error("Failed to fetch containers from WUD")
                return []


class WUDContainerSensor(Entity):
    """Representation of a What's Up Docker container sensor."""

    def __init__(self, container, config_entry: ConfigEntry, instance_name: str):
        """Initialize the sensor."""
        self._container = container
        self._config_entry = config_entry
        self._name = f"{container['name']} Update Available"
        self._state = container.get("updateAvailable", False)
        self._unique_id = f"wud_{container['id']}_update_available"
        self._instance_name = instance_name
        self._device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": instance_name,
            "manufacturer": "What's Up Docker",
            "model": "Docker Instance",
        }

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return "Yes" if self._state else "No"

    @property
    def device_info(self):
        return self._device_info

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        current_version = self._container.get("version", "unknown")

        # WUD lagrar nya versionen i "result" när updateAvailable är True
        result = self._container.get("result", {}) or {}
        new_version = result.get("tag") if result else None

        return {
            "container_id": self._container["id"],
            "current_version": current_version,
            "new_version": new_version if new_version else "unknown",
            "update_available": self._state,
            "image": self._container.get("image", "unknown"),
        }

    async def async_update(self):
        """Fetch updated data from the API."""
        containers = await get_containers(
            self._config_entry.data["host"],
            self._config_entry.data["port"],
        )
        for container in containers:
            if container["id"] == self._container["id"]:
                self._container = container
                self._state = container.get("updateAvailable", False)
                break
