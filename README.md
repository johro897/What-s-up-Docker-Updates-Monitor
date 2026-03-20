# What's Up Docker Updates Monitor

## About

This integration fetches container information from a [What's Up Docker](https://github.com/getwud/wud) instance using its REST API, creating one sensor per monitored container indicating whether updates are available.

### Features

- **Per-container sensors** — tracks update status, current version, and new version for each container
- **Version details** — shows `current_version` and `new_version` using OCI image labels for accurate version strings
- **Update age** — when an update is available, `available_since` and `days_available` show how long the new version has been out
- **Compose project grouping** — containers sharing the same Docker Compose project are grouped under one device in HA, making setups with many containers (e.g. multiple game servers) much easier to manage
- **Multi-instance support** — add multiple WUD instances, each gets its own set of devices and sensors
- **Connection validation** — the integration tests the connection to WUD before saving, with clear error feedback if it fails

### Sensor attributes

| Attribute | Description |
|---|---|
| `current_version` | Currently running version |
| `new_version` | Available update version (`–` if none) |
| `available_since` | When the new image was published (UTC) |
| `days_available` | Days since the new version became available |
| `semver_diff` | Severity of update: `patch`, `minor` or `major` |
| `image` | Full image name (e.g. `esphome/esphome`) |
| `registry` | Registry name (e.g. `ghcr.public`, `hub.public`) |
| `compose_project` | Docker Compose project name |
| `status` | Container status (e.g. `running`) |

---

## Installation

### Requirements

- A Home Assistant instance with [HACS](https://hacs.xyz/) installed
- A running instance of [What's Up Docker](https://github.com/getwud/wud) (tested with WUD 8.2+)

### HACS Installation

Search for **"What's Up Docker Updates Monitor"** in the HACS store. If it doesn't appear, add this repository as a [HACS custom repository](https://hacs.xyz/docs/faq/custom_repositories).

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/pveiga90/What-s-up-Docker-Updates-Monitor)

---

## Configuration

After installation, add the integration via **Settings → Devices & Services → Add Integration** and search for *What's Up Docker*.

When prompted, provide:

| Field | Description |
|---|---|
| **Host** | IP address or hostname of your WUD instance |
| **Port** | WUD web UI port (default: `3000`) |
| **Instance Name** | A friendly name for this WUD instance (used as the device name in HA) |

Settings can be changed later via the integration's **Configure** button.

### WUD container labels

For WUD to monitor a container, make sure it has the `wud.watch: "true"` label in your `docker-compose.yml`:

```yaml
labels:
  - "wud.watch=true"
```

To stay on the same version track and avoid pre-release or variant tags, use `wud.tag.include`:

```yaml
labels:
  - "wud.watch=true"
  - "wud.tag.include=^2\\.0\\.\\d+$"       # SemVer: stay on 2.0.x
  - "wud.tag.include=^20[0-9]{2}\\.[0-9]+\\.[0-9]+$"  # CalVer: stay on same year.month.x
```

---

## Troubleshooting

If the integration fails to connect, verify that the WUD API is reachable:

```
http://<wud_host>:<wud_port>/api/containers
```

This should return a JSON array of your monitored containers. If it doesn't, check that WUD is running and that no firewall is blocking the port.

---

## Contributions

Contributions are welcome! Feel free to open an issue or pull request.
