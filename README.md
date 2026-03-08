# pi-sysmon

A Raspberry Pi system monitor with three components: a live terminal UI, a background SQLite logger, and a Flask web dashboard.

---

## Components

### 1. `sysmon.py` — Terminal Monitor

A full-screen terminal dashboard that displays live system stats, refreshing every 2 seconds.

**Displays:**
- CPU usage (overall % and per-core) with frequency
- RAM and swap usage with progress bars
- Disk usage and total I/O
- Network bytes sent/received
- CPU temperature (colour-coded green/yellow/red)
- Top 8 processes by CPU usage

**Dependencies:** `psutil`, `rich`

---

### 2. `logger.py` — Background SQLite Logger

Runs silently in the background, sampling system stats every 60 seconds and writing them to a SQLite database (`sysmon.db`).

**Records:**
| Column | Description |
|---|---|
| `timestamp` | Unix timestamp (primary key) |
| `cpu_percent` | CPU usage % |
| `mem_percent` | Memory usage % |
| `mem_used_mb` | Memory used in MB |
| `swap_percent` | Swap usage % |
| `disk_percent` | Disk usage % |
| `temp_c` | CPU temperature in °C |

**Dependencies:** `psutil`

---

### 3. `app.py` + `templates/index.html` — Web Dashboard

A Flask web server that serves a dark-themed dashboard. Binds to `127.0.0.1` (localhost only) for security — use a reverse proxy such as nginx to expose it on the network.

**Features:**
- Live stat cards (CPU, memory, disk, temperature, swap) — refreshes every 5 seconds
- 4 time-series charts showing the last 24 hours of data from `sysmon.db` — refreshes every 60 seconds
- Colour-coded values (green/yellow/red) based on thresholds
- Uptime counter

**API endpoints:**

| Endpoint | Description |
|---|---|
| `GET /` | Serves the dashboard HTML |
| `GET /api/live` | Returns current stats as JSON (via psutil) |
| `GET /api/history` | Returns last 24h of logged stats from SQLite as JSON |

**Dependencies:** `psutil`, `flask`

---

## How They Work Together

```
Hardware (CPU · Memory · Disk · Network · Temp Sensor)
              │
              │ psutil
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
sysmon.py          logger.py
Terminal UI        Runs in background
Updates every 2s   Logs every 60s
                        │
                        ▼
                    sysmon.db (SQLite)
                        │
                        │ SQL query
                        ▼
                    app.py (Flask :5000)
                        │
                        │ HTTP
                        ▼
                    Browser Dashboard
                    /api/live    ◄── psutil (every 5s)
                    /api/history ◄── SQLite (every 60s)
```

- `sysmon.py` and `logger.py` both read hardware independently via psutil
- `logger.py` is the only component that writes to `sysmon.db`
- `app.py` reads from both psutil (for live stats) and `sysmon.db` (for history)
- All three start automatically on boot via cron

---

## Installation

### Requirements

- Raspberry Pi running Raspberry Pi OS
- Python 3.x
- pip

### 1. Clone the repository

```bash
git clone https://github.com/alexsmith3816/pi-sysmon.git
cd pi-sysmon
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install psutil rich flask
```

---

## Running Each Component

### Terminal Monitor

```bash
source .venv/bin/activate
python3 sysmon.py
```

Press `Ctrl+C` to quit.

---

### SQLite Logger

```bash
source .venv/bin/activate
python3 logger.py
```

Logs are written to `sysmon.db` every 60 seconds. Press `Ctrl+C` to stop.

To query the database directly:

```bash
sqlite3 sysmon.db "SELECT datetime(timestamp,'unixepoch','localtime'), cpu_percent, mem_percent, temp_c FROM stats ORDER BY timestamp DESC LIMIT 10;"
```

---

### Web Dashboard

```bash
source .venv/bin/activate
python3 app.py
```

The dashboard is accessible locally at:

```
http://127.0.0.1:5000
```

To access it from another device on the network, set up a reverse proxy (e.g. nginx) pointing to `127.0.0.1:5000`.

---

## Auto-start on Boot

All three components are configured to start automatically on boot via cron.

To view or edit the cron jobs:

```bash
crontab -e
```

The entries look like this:

```
@reboot DISPLAY=:0 lxterminal -e /home/alex/code/sysmon.sh
@reboot /home/alex/code/.venv/bin/python3 /home/alex/code/logger.py >> /home/alex/code/logger.log 2>&1
@reboot /home/alex/code/.venv/bin/python3 /home/alex/code/app.py >> /home/alex/code/app.log 2>&1
```

Logs for the background processes are written to `logger.log` and `app.log` in the project directory.
