#!/usr/bin/env python3
"""Log system stats to SQLite every 60 seconds."""

import logging
import time
import sqlite3
import psutil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DB_PATH = "/home/alex/code/sysmon.db"
INTERVAL = 60  # seconds


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            timestamp   INTEGER PRIMARY KEY,
            cpu_percent REAL,
            mem_percent REAL,
            mem_used_mb REAL,
            swap_percent REAL,
            disk_percent REAL,
            temp_c      REAL
        )
    """)
    conn.commit()


def get_temp():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        for entries in temps.values():
            if entries:
                return entries[0].current
    except AttributeError:
        pass
    return None


def collect():
    try:
        cpu = psutil.cpu_percent(interval=1)
    except Exception:
        cpu = None

    try:
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used_mb = mem.used / 1024 / 1024
    except Exception:
        mem_percent = mem_used_mb = None

    try:
        swap_percent = psutil.swap_memory().percent
    except Exception:
        swap_percent = None

    try:
        disk_percent = psutil.disk_usage("/").percent
    except Exception:
        disk_percent = None

    return (
        int(time.time()),
        cpu,
        mem_percent,
        mem_used_mb,
        swap_percent,
        disk_percent,
        get_temp(),
    )


def main():
    with sqlite3.connect(DB_PATH) as conn:
        init_db(conn)
        logging.info(f"Logging to {DB_PATH} every {INTERVAL}s")
        try:
            while True:
                row = collect()
                conn.execute(
                    "INSERT OR REPLACE INTO stats VALUES (?,?,?,?,?,?,?)", row
                )
                conn.commit()
                logging.info(f"CPU {row[1]:.1f}%  MEM {row[2]:.1f}%  TEMP {f'{row[6]:.1f}°C' if row[6] is not None else 'N/A'}")
                time.sleep(INTERVAL)
        except KeyboardInterrupt:
            logging.info("Stopped.")


if __name__ == "__main__":
    main()
