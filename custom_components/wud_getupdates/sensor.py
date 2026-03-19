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

    sensors = [WUDContainerSensor(c, config_entry, instance_name) for c in containers]
    async_add_entities(sensors, True)


async def get_containers(host, port):
    """Fetch containers from the WUD API."""
    url = f"http://{host}:{port}/api/containers"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data if isinstance(data, list) else data.get("items", [])
            _LOGGER.error("Failed to fetch containers from WUD (HTTP %s)", response.status)
            return []


class WUDContainerSensor(Entity):
    """Representation of a What's Up Docker container sensor."""

    def __init__(self, container, config_entry: ConfigEntry, instance_name: str):
        self._container = container
        self._config_entry = config_entry
        self._instance_name = instance_name
        self._name = f"{container['name']} Update Available"
        self._unique_id = f"wud_{container['id']}_update_available"
        self._device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": instance_name,
            "manufacturer": "What's Up Docker",
            "model": "Docker Instance",
        }

    def _get_current_version(self):
        """
        Hämta nuvarande version.
        Föredrar org.opencontainers.image.version (innehåller full version, t.ex. 2026.2.4)
        framför image.tag.value som kan vara förkortad (t.ex. 2026.2).
        """
        labels = self._container.get("labels", {}) or {}
        oci_version = labels.get("org.opencontainers.image.version")
        if oci_version:
            return oci_version
        image = self._container.get("image", {}) or {}
        tag = image.get("tag", {}) or {}
        return tag.get("value", "unknown")

    def _get_new_version(self):
        """Hämta nya versionen från updateKind.remoteValue eller result.tag."""
        update_kind = self._container.get("updateKind", {}) or {}
        remote = update_kind.get("remoteValue")
        if remote:
            return remote
        result = self._container.get("result", {}) or {}
        tag = result.get("tag")
        if tag and tag != self._get_current_version():
            return tag
        return None

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return "Yes" if self._container.get("updateAvailable", False) else "No"

    @property
    def device_info(self):
        return self._device_info

    @property
    def extra_state_attributes(self):
        update_kind = self._container.get("updateKind", {}) or {}
        current = self._get_current_version()
        new = self._get_new_version()

        image = self._container.get("image", {}) or {}
        registry = image.get("registry", {}) or {}

        return {
            "container_id": self._container["id"],
            "image": image.get("name", "unknown"),
            "registry": registry.get("name", "unknown"),
            "current_version": current,
            "new_version": new if new else "–",
            "update_available": self._container.get("updateAvailable", False),
            "semver_diff": update_kind.get("semverDiff"),
            "status": self._container.get("status", "unknown"),
        }

    async def async_update(self):
        """Hämta uppdaterad data från WUD API."""
        containers = await get_containers(
            self._config_entry.data["host"],
            self._config_entry.data["port"],
        )
        for c in containers:
            if c["id"] == self._container["id"]:
                self._container = c
                break
