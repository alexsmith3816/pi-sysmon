#!/usr/bin/env python3
"""Raspberry Pi system monitor — displays CPU, memory, disk, network, and temperature."""

import time
import psutil
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.live import Live
from rich.text import Text


def get_cpu():
    try:
        percent = psutil.cpu_percent(interval=None)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        freq = psutil.cpu_freq()
        freq_str = f"{freq.current:.0f} MHz" if freq else "N/A"
    except Exception:
        return Panel("Unavailable", title="CPU", border_style="cyan")
    bar = make_bar(percent)
    return Panel(
        f"{bar} [bold]{percent:.1f}%[/bold]\nFreq: {freq_str}\nCores: {', '.join(f'{c:.0f}%' for c in per_core)}",
        title="CPU",
        border_style="cyan",
    )


def get_memory():
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
    except Exception:
        return Panel("Unavailable", title="Memory", border_style="green")
    mem_bar = make_bar(mem.percent)
    swap_bar = make_bar(swap.percent)
    return Panel(
        f"RAM:  {mem_bar} [bold]{mem.percent:.1f}%[/bold]  {fmt_bytes(mem.used)} / {fmt_bytes(mem.total)}\n"
        f"Swap: {swap_bar} [bold]{swap.percent:.1f}%[/bold]  {fmt_bytes(swap.used)} / {fmt_bytes(swap.total)}",
        title="Memory",
        border_style="green",
    )


def get_disk():
    try:
        disk = psutil.disk_usage("/")
        io = psutil.disk_io_counters()
    except Exception:
        return Panel("Unavailable", title="Disk (/)", border_style="yellow")
    bar = make_bar(disk.percent)
    io_str = f"Read: {fmt_bytes(io.read_bytes)}  Write: {fmt_bytes(io.write_bytes)}" if io else ""
    return Panel(
        f"{bar} [bold]{disk.percent:.1f}%[/bold]  {fmt_bytes(disk.used)} / {fmt_bytes(disk.total)}\n{io_str}",
        title="Disk (/)",
        border_style="yellow",
    )


def get_network():
    try:
        net = psutil.net_io_counters()
        if net is None:
            raise ValueError("No network counters available")
    except Exception:
        return Panel("Unavailable", title="Network", border_style="magenta")
    return Panel(
        f"Sent:     {fmt_bytes(net.bytes_sent)}\n"
        f"Received: {fmt_bytes(net.bytes_recv)}\n"
        f"Packets sent/recv: {net.packets_sent} / {net.packets_recv}",
        title="Network",
        border_style="magenta",
    )


def get_temperature():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return Panel("Not available", title="Temperature", border_style="red")
        lines = []
        for name, entries in temps.items():
            for entry in entries:
                label = entry.label or name
                color = "red" if entry.current >= 80 else "yellow" if entry.current >= 70 else "green"
                lines.append(f"{label}: [{color}]{entry.current:.1f}°C[/{color}]")
        return Panel("\n".join(lines) or "No sensors found", title="Temperature", border_style="red")
    except AttributeError:
        return Panel("Not supported", title="Temperature", border_style="red")


def get_processes(n=8):
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("PID", style="dim", width=7)
    table.add_column("Name", width=20)
    table.add_column("CPU%", justify="right", width=6)
    table.add_column("MEM%", justify="right", width=6)
    table.add_column("Status", width=10)

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: x["cpu_percent"] or 0, reverse=True)
    for p in procs[:n]:
        cpu = p["cpu_percent"] or 0
        mem = p["memory_percent"] or 0
        cpu_color = "red" if cpu > 50 else "yellow" if cpu > 20 else "white"
        table.add_row(
            str(p["pid"]),
            (p["name"] or "")[:20],
            f"[{cpu_color}]{cpu:.1f}[/{cpu_color}]",
            f"{mem:.1f}",
            p["status"] or "",
        )

    return Panel(table, title=f"Top {n} Processes (by CPU)", border_style="blue")


def make_bar(percent, width=20):
    percent = max(0.0, min(100.0, float(percent)))
    filled = int(width * percent / 100)
    color = "red" if percent >= 90 else "yellow" if percent >= 70 else "green"
    bar = f"[{color}]{'█' * filled}[/{color}]{'░' * (width - filled)}"
    return bar


def fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def build_layout():
    top = Columns([get_cpu(), get_memory()], equal=True)
    mid = Columns([get_disk(), get_network(), get_temperature()], equal=True)
    procs = get_processes()
    try:
        uptime = time.time() - psutil.boot_time()
        h, m = divmod(int(uptime) // 60, 60)
        d, h = divmod(h, 24)
        uptime_str = f"{d}d {h}h {m}m"
    except Exception:
        uptime_str = "N/A"
    footer = Text(f"Uptime: {uptime_str}   Refresh: 2s   Press Ctrl+C to quit", justify="center", style="dim")
    return Group(top, mid, procs, footer)


def main():
    console = Console()
    # Warm up cpu_percent (first call always returns 0)
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)

    with Live(build_layout(), console=console, refresh_per_second=0.5, screen=True) as live:
        while True:
            time.sleep(2)
            live.update(build_layout())


if __name__ == "__main__":
    main()
