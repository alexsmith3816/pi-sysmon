#!/usr/bin/env python3
"""Flask web dashboard for pi-sysmon stats."""

import os
import sqlite3
import time
import psutil
from flask import Flask, jsonify, render_template

app = Flask(__name__)
DB_PATH = "/home/alex/code/sysmon.db"


def query_db(sql, args=()):
    if not os.path.exists(DB_PATH):
        return []
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, args).fetchall()
    con.close()
    return [dict(r) for r in rows]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/history")
def history():
    """Last 24 hours of logged stats."""
    since = int(time.time()) - 86400
    rows = query_db(
        "SELECT timestamp, cpu_percent, mem_percent, disk_percent, temp_c "
        "FROM stats WHERE timestamp >= ? ORDER BY timestamp ASC",
        (since,),
    )
    return jsonify(rows)


@app.route("/api/live")
def live():
    """Current system stats."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    swap = psutil.swap_memory()

    temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for entries in temps.values():
                if entries:
                    temp = entries[0].current
                    break
    except AttributeError:
        pass

    uptime = int(time.time() - psutil.boot_time())
    h, m = divmod(uptime // 60, 60)
    d, h = divmod(h, 24)

    return jsonify({
        "cpu_percent": cpu,
        "mem_percent": mem.percent,
        "mem_used_gb": round(mem.used / 1024 ** 3, 2),
        "mem_total_gb": round(mem.total / 1024 ** 3, 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1024 ** 3, 2),
        "disk_total_gb": round(disk.total / 1024 ** 3, 2),
        "swap_percent": swap.percent,
        "temp_c": temp,
        "uptime": f"{d}d {h}h {m}m",
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
