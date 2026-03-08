#!/usr/bin/env python3
"""Log system stats to SQLite every 60 seconds."""

import time
import sqlite3
import psutil

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
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    temp = get_temp()
    return (
        int(time.time()),
        cpu,
        mem.percent,
        mem.used / 1024 / 1024,
        swap.percent,
        disk.percent,
        temp,
    )


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    print(f"Logging to {DB_PATH} every {INTERVAL}s — Ctrl+C to stop")
    try:
        while True:
            row = collect()
            conn.execute(
                "INSERT OR REPLACE INTO stats VALUES (?,?,?,?,?,?,?)", row
            )
            conn.commit()
            print(f"[{time.strftime('%H:%M:%S')}] CPU {row[1]:.1f}%  MEM {row[2]:.1f}%  TEMP {f'{row[6]:.1f}°C' if row[6] else 'N/A'}")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
