"""
topology.py

This file describes the SHAPE of our simulated enterprise network:
which sites exist, which devices live at each site, and which WAN
links connect them. Nothing in here generates telemetry yet -
this is just the "map" that the simulator will read from.

Why a separate file? Because the topology is configuration, not logic.
Later, if we want to add a 6th branch or change a link type, we only
edit this file - the simulator code doesn't change at all.
"""

from dataclasses import dataclass, field
from enum import Enum


class DeviceRole(Enum):
    CORE_ROUTER = "core_router"
    FIREWALL = "firewall"
    MPLS_EDGE = "mpls_edge_router"
    SDWAN_EDGE = "sdwan_edge_router"
    WAN_EDGE = "wan_edge_router"
    LAN_SWITCH = "lan_switch"


class LinkType(Enum):
    MPLS = "mpls"
    BROADBAND = "broadband_internet"
    LTE = "lte_5g_backup"
    IPSEC_VPN = "ipsec_vpn"


@dataclass
class Device:
    device_id: str          # short unique code, e.g. "HQ-CORE-01"
    name: str                # human readable, e.g. "Chennai HQ Core Router"
    site: str                # e.g. "Chennai HQ"
    role: DeviceRole
    # "Normal" operating baselines - same idea as WANLink baselines.
    # A core router naturally runs hotter (more CPU/memory) than an
    # idle LAN switch, so these differ per device below.
    baseline_cpu_pct: float
    baseline_memory_pct: float


@dataclass
class WANLink:
    link_id: str             # e.g. "MPLS-HQ-BLR"
    name: str                # e.g. "Chennai HQ <-> Bangalore MPLS"
    site_a: str
    site_b: str
    link_type: LinkType
    # "Normal" operating baselines for this link - the simulator
    # will generate values that hover around these, not exact copies.
    baseline_latency_ms: float
    baseline_jitter_ms: float
    baseline_packet_loss_pct: float
    baseline_utilization_pct: float


# ---------------------------------------------------------------------
# SITES
# ---------------------------------------------------------------------

SITES = [
    "Chennai HQ",
    "Bangalore",
    "Hyderabad",
    "Mumbai",
    "Delhi",
]

# ---------------------------------------------------------------------
# DEVICES
# ---------------------------------------------------------------------

DEVICES = [
    # Chennai HQ - core/firewall/edge routers run hotter (more traffic
    # passes through them) than a branch switch
    Device("HQ-CORE-01", "Chennai HQ Core Router", "Chennai HQ", DeviceRole.CORE_ROUTER,
           baseline_cpu_pct=45, baseline_memory_pct=55),
    Device("HQ-FW-01", "Chennai HQ Firewall", "Chennai HQ", DeviceRole.FIREWALL,
           baseline_cpu_pct=40, baseline_memory_pct=50),
    Device("HQ-MPLS-01", "Chennai HQ MPLS Edge Router", "Chennai HQ", DeviceRole.MPLS_EDGE,
           baseline_cpu_pct=35, baseline_memory_pct=45),
    Device("HQ-SDWAN-01", "Chennai HQ SD-WAN Edge Router", "Chennai HQ", DeviceRole.SDWAN_EDGE,
           baseline_cpu_pct=35, baseline_memory_pct=45),

    # Branches - each gets a WAN edge router + LAN switch
    Device("BLR-EDGE-01", "Bangalore WAN Edge Router", "Bangalore", DeviceRole.WAN_EDGE,
           baseline_cpu_pct=30, baseline_memory_pct=40),
    Device("BLR-SW-01", "Bangalore LAN Switch", "Bangalore", DeviceRole.LAN_SWITCH,
           baseline_cpu_pct=15, baseline_memory_pct=25),

    Device("HYD-EDGE-01", "Hyderabad WAN Edge Router", "Hyderabad", DeviceRole.WAN_EDGE,
           baseline_cpu_pct=30, baseline_memory_pct=40),
    Device("HYD-SW-01", "Hyderabad LAN Switch", "Hyderabad", DeviceRole.LAN_SWITCH,
           baseline_cpu_pct=15, baseline_memory_pct=25),

    Device("MUM-EDGE-01", "Mumbai WAN Edge Router", "Mumbai", DeviceRole.WAN_EDGE,
           baseline_cpu_pct=32, baseline_memory_pct=42),
    Device("MUM-SW-01", "Mumbai LAN Switch", "Mumbai", DeviceRole.LAN_SWITCH,
           baseline_cpu_pct=15, baseline_memory_pct=25),

    Device("DEL-EDGE-01", "Delhi WAN Edge Router", "Delhi", DeviceRole.WAN_EDGE,
           baseline_cpu_pct=33, baseline_memory_pct=43),
    Device("DEL-SW-01", "Delhi LAN Switch", "Delhi", DeviceRole.LAN_SWITCH,
           baseline_cpu_pct=15, baseline_memory_pct=25),
]

# ---------------------------------------------------------------------
# WAN LINKS
# Each branch gets: 1 primary MPLS link to HQ, 1 secondary broadband
# (IPSec VPN over internet) to HQ. Delhi additionally gets an LTE
# backup, to demonstrate a 3-transport SD-WAN scenario for variety.
# ---------------------------------------------------------------------

WAN_LINKS = [
    WANLink("MPLS-HQ-BLR", "HQ <-> Bangalore MPLS", "Chennai HQ", "Bangalore",
            LinkType.MPLS, baseline_latency_ms=18, baseline_jitter_ms=2,
            baseline_packet_loss_pct=0.05, baseline_utilization_pct=35),
    WANLink("VPN-HQ-BLR", "HQ <-> Bangalore IPSec VPN (Broadband)", "Chennai HQ", "Bangalore",
            LinkType.IPSEC_VPN, baseline_latency_ms=28, baseline_jitter_ms=5,
            baseline_packet_loss_pct=0.15, baseline_utilization_pct=20),

    WANLink("MPLS-HQ-HYD", "HQ <-> Hyderabad MPLS", "Chennai HQ", "Hyderabad",
            LinkType.MPLS, baseline_latency_ms=15, baseline_jitter_ms=2,
            baseline_packet_loss_pct=0.05, baseline_utilization_pct=30),
    WANLink("VPN-HQ-HYD", "HQ <-> Hyderabad IPSec VPN (Broadband)", "Chennai HQ", "Hyderabad",
            LinkType.IPSEC_VPN, baseline_latency_ms=24, baseline_jitter_ms=4,
            baseline_packet_loss_pct=0.12, baseline_utilization_pct=18),

    WANLink("MPLS-HQ-MUM", "HQ <-> Mumbai MPLS", "Chennai HQ", "Mumbai",
            LinkType.MPLS, baseline_latency_ms=22, baseline_jitter_ms=3,
            baseline_packet_loss_pct=0.06, baseline_utilization_pct=40),
    WANLink("VPN-HQ-MUM", "HQ <-> Mumbai IPSec VPN (Broadband)", "Chennai HQ", "Mumbai",
            LinkType.IPSEC_VPN, baseline_latency_ms=32, baseline_jitter_ms=6,
            baseline_packet_loss_pct=0.18, baseline_utilization_pct=22),

    WANLink("MPLS-HQ-DEL", "HQ <-> Delhi MPLS", "Chennai HQ", "Delhi",
            LinkType.MPLS, baseline_latency_ms=35, baseline_jitter_ms=4,
            baseline_packet_loss_pct=0.07, baseline_utilization_pct=45),
    WANLink("VPN-HQ-DEL", "HQ <-> Delhi IPSec VPN (Broadband)", "Chennai HQ", "Delhi",
            LinkType.IPSEC_VPN, baseline_latency_ms=40, baseline_jitter_ms=7,
            baseline_packet_loss_pct=0.20, baseline_utilization_pct=25),
    WANLink("LTE-HQ-DEL", "HQ <-> Delhi LTE/5G Backup", "Chennai HQ", "Delhi",
            LinkType.LTE, baseline_latency_ms=55, baseline_jitter_ms=12,
            baseline_packet_loss_pct=0.40, baseline_utilization_pct=5),
]


if __name__ == "__main__":
    # Quick sanity check when you run this file directly
    print(f"Sites: {len(SITES)}")
    print(f"Devices: {len(DEVICES)}")
    print(f"WAN Links: {len(WAN_LINKS)}")
