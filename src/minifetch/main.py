#!/usr/bin/env python3
# minifetch - A minimal system information tool

import platform
import socket
from datetime import datetime, timedelta

import humanize
import psutil
import typer
from psutil._common import bytes2human
from pyfiglet import Figlet
from rich import style
from rich.bar import Bar
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()
app = typer.Typer()

header_style = style.Style(
    color="white",
    bold=True,
    dim=False,
    italic=False,
    underline=False,
    blink=False,
    reverse=False,
)


THRESHOLD_GREEN = 50
THRESHOLD_YELLOW = 80


def color_from_percent(percent: float) -> str:
    if percent < THRESHOLD_GREEN:
        return "green"
    if percent < THRESHOLD_YELLOW:
        return "yellow"
    return "red"


def style_from_percent(percent: float) -> style.Style:
    return style.Style(color=color_from_percent(percent), bold=True)


def style_from_value(value: float, total: float) -> style.Style:
    percent = value / total * 100
    return style_from_percent(percent)


def color_from_value(value: float, total: float) -> str:
    percent = value / total * 100
    return color_from_percent(percent)


def show_hostname() -> None:
    host_name: str = socket.gethostname()
    f = Figlet(font="slant")
    console.print(f.renderText(f"{host_name}"))


def show_os() -> None:
    os_name: str = platform.system()
    os_version: str = platform.release()
    os_arch: str = platform.machine()
    os_info: str = f"{os_name} {os_version} ({os_arch})"
    console.print(Text("OS:\t", style=header_style), os_info)
    console.print()


def show_cpu() -> None:
    cpu_count = psutil.cpu_count()
    if not cpu_count:
        cpu_count = 1
    load_avg = [x / cpu_count for x in psutil.getloadavg()]
    cpu_percentages = psutil.cpu_percent(interval=0.0, percpu=True)
    table = Table(
        show_header=False,
        box=None,
        pad_edge=False,
        title=Text("CPU Load", style=header_style),
    )
    table.add_column("Core", justify="left")
    table.add_column("Load", justify="left")
    table.add_column("Percent", justify="left")
    for i, percent in enumerate(cpu_percentages):
        gauge = Bar(
            100,
            begin=0,
            end=percent,
            width=50,
            bgcolor="grey0",
            color=color_from_percent(percent),
        )
        table.add_row(f"Core {i}", gauge, f"{percent:.1f}%")
    console.print(table)

    console.print()
    table = Table(
        show_header=False,
        box=None,
        pad_edge=False,
        title=Text("Load Average", style=header_style),
    )
    table.add_column("1 min", justify="left")
    table.add_column("5 min", justify="left")
    table.add_column("15 min", justify="left")
    table.add_row(
        Text(f"{load_avg[0]:.2f}", style=style_from_value(load_avg[0], 1.0)),
        Text(f"{load_avg[1]:.2f}", style=style_from_value(load_avg[1], 1.0)),
        Text(f"{load_avg[2]:.2f}", style=style_from_value(load_avg[2], 1.0)),
    )
    console.print(table)


def show_uptime() -> None:
    console.print(
        Text("Uptime", style=header_style),
    )
    boot_time: datetime = datetime.fromtimestamp(psutil.boot_time())  # noqa: DTZ006
    time_now: datetime = datetime.now()  # noqa: DTZ005
    uptime: timedelta = time_now - boot_time
    uptime_text = humanize.precisedelta(uptime, minimum_unit="minutes", format="%0.0f")
    console.print(f"System is up [green]{uptime_text}[/green]")


def show_memory() -> None:
    vmem = psutil.virtual_memory()
    smem = psutil.swap_memory()

    vmem_used = bytes2human(vmem.used)
    vmem_total = bytes2human(vmem.total)
    smem_used = bytes2human(smem.used)
    smem_total = bytes2human(smem.total)
    table = Table(
        show_header=False,
        box=None,
        pad_edge=False,
        title=Text("Memory Usage", style=header_style),
    )
    table.add_column("Type", justify="left")
    table.add_column("Usage", justify="left")
    table.add_column("Percent", justify="left")
    table.add_row(
        "RAM",
        Bar(
            100,
            begin=0,
            end=vmem.percent,
            width=50,
            color=color_from_percent(vmem.percent),
        ),
        f"{vmem.percent:.1f}%",
    )
    table.add_row(
        "Swap",
        Bar(
            100,
            begin=0,
            end=smem.percent,
            width=50,
            color=color_from_percent(smem.percent),
        ),
        f"{smem.percent:.1f}%",
    )
    console.print(table)
    console.print(f"RAM: {vmem_used} / {vmem_total}")
    console.print(f"Swap: {smem_used} / {smem_total}" if smem.total else "")
    console.print()


def show_disk() -> None:
    disk_partitions = psutil.disk_partitions()
    table = Table(
        show_header=False,
        box=None,
        pad_edge=False,
        title=Text("Disk Usage", style=header_style),
    )
    table.add_column("Type", justify="left")
    table.add_column("Usage", justify="left")
    table.add_column("Percent", justify="left")
    for partition in disk_partitions:
        if "loop" in partition.mountpoint:
            continue
        if partition.fstype == "":
            continue
        if "dontbrowse" in partition.opts and not partition.mountpoint.startswith(
            "/System/Volumes/Data"
        ):
            continue

        partition_usage = psutil.disk_usage(partition.mountpoint)
        table.add_row(
            (
                f"{partition.device} on {partition.mountpoint}"
                if partition.device != partition.mountpoint
                else partition.device
            ),
            Bar(
                100,
                begin=0,
                end=partition_usage.percent,
                width=50,
                color=color_from_percent(partition_usage.percent),
            ),
            f"{bytes2human(partition_usage.used)} / {bytes2human(partition_usage.total)}",
        )
    console.print(table)
    console.print()


def show_network_interfaces() -> None:
    if_addrs = psutil.net_if_addrs()
    if_stats = psutil.net_if_stats()

    table = Table(
        title=Text("Network Interfaces", style=header_style),
    )
    table.add_column("Interface", justify="left")
    table.add_column("Addresses", justify="left")
    table.add_column("Speed", justify="left")
    table.add_column("Type", justify="left")

    for nic, addrs in if_addrs.items():
        addresses = []
        if nic.startswith("lo") or not addrs or not if_stats[nic].isup:
            continue

        addresses = [addr for addr in addrs if addr.family == socket.AF_INET]
        if not addresses:
            continue
        possible_vpn: bool = any(a for a in addrs if a.ptp)

        table.add_row(
            nic,
            "\n".join([f"{ip.address}" for ip in addresses]),
            f"{if_stats[nic].speed} Mbps" if if_stats[nic].speed else "",
            ":closed_lock_with_key:" if possible_vpn else "",
        )
    console.print(table)


def show_network_statistics() -> None:
    net_io = psutil.net_io_counters(pernic=True)
    table = Table(
        title=Text("Network Statistics", style=header_style),
    )
    table.add_column("Interface", justify="left")
    table.add_column("Sent", justify="left")
    table.add_column("Received", justify="left")
    for nic, stats in net_io.items():
        if nic.startswith("lo"):
            continue
        if not stats:
            continue
        if not stats.bytes_sent and not stats.bytes_recv:
            continue
        if stats.bytes_sent <= 0 and stats.bytes_recv <= 0:
            continue
        table.add_row(
            nic,
            bytes2human(stats.bytes_sent),
            bytes2human(stats.bytes_recv),
        )
    console.print(table)


def show_temperatures() -> None:
    if not hasattr(psutil, "sensors_temperatures"):
        return
    temps = psutil.sensors_temperatures()
    if not temps:
        return

    table = Table(
        title=Text("Temperatures", style=header_style),
    )
    table.add_column("Sensor", justify="left")
    table.add_column("Temperature", justify="left")

    for name, entries in temps.items():
        temps = [entry for entry in entries if entry.label and entry.current]

        for entry in entries:
            temp_value = Text(
                f"{entry.current}°C",
                style=style_from_value(entry.current, entry.critical or 100),
            )

            if entry.current is None:
                continue
            table.add_row(
                name,
                temp_value,
            )
    console.print(table)


@app.command()
def main() -> None:
    show_hostname()
    show_os()
    show_uptime()
    show_cpu()
    show_memory()
    show_disk()
    show_network_interfaces()
    show_network_statistics()
    show_temperatures()


if __name__ == "__main__":
    main()
