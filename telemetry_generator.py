"""
telemetry_generator.py

This module turns a WANLink's static baseline values into a stream of
realistic, fluctuating metric readings over time.

KEY IDEA: real network metrics drift smoothly, they don't jump randomly
every second. If latency is 20ms now, half a second later it's more
likely to be 19-21ms than suddenly 40ms. We simulate this using a
"mean-reverting random walk": each new value is nudged a little from
the PREVIOUS value, but gently pulled back toward the link's baseline
over time (so it doesn't drift off to nonsense values forever).

This is the same basic idea used in finance to simulate stock prices
(Ornstein-Uhlenbeck process) - just applied to network metrics instead.
"""

import random
from dataclasses import dataclass, field
from topology import WANLink, WAN_LINKS, Device, DEVICES


@dataclass
class LinkState:
    """
    Tracks the CURRENT live value of each metric for a link, so the
    next reading can be generated relative to the last one instead of
    from scratch. One LinkState exists per WANLink for the life of
    the simulation.
    """
    link: WANLink
    current_latency_ms: float = field(init=False)
    current_jitter_ms: float = field(init=False)
    current_packet_loss_pct: float = field(init=False)
    current_utilization_pct: float = field(init=False)

    def __post_init__(self):
        # Start each metric right at its baseline
        self.current_latency_ms = self.link.baseline_latency_ms
        self.current_jitter_ms = self.link.baseline_jitter_ms
        self.current_packet_loss_pct = self.link.baseline_packet_loss_pct
        self.current_utilization_pct = self.link.baseline_utilization_pct


def _mean_reverting_step(current: float, baseline: float,
                          volatility: float, pull_strength: float = 0.15) -> float:
    """
    Computes the next value for a metric.

    - `volatility` controls how "jumpy" the metric is per step
    - `pull_strength` controls how strongly it's pulled back toward baseline
      (0 = pure random drift / could wander forever, 1 = snaps back instantly)

    This is the one function doing the actual "realistic fluctuation" math.
    Everything else in this file is just bookkeeping around it.
    """
    random_shock = random.gauss(0, volatility)
    pull_toward_baseline = (baseline - current) * pull_strength
    next_value = current + random_shock + pull_toward_baseline
    return max(next_value, 0)  # metrics can't go negative


def generate_next_reading(state: LinkState) -> dict:
    """
    Advances a link's state by one time-step and returns the new
    reading as a plain dict - this is the shape that will eventually
    get written to the database or printed to a CSV.
    """
    link = state.link

    # Volatility is scaled relative to each metric's baseline, so a
    # naturally noisier link (e.g. LTE) fluctuates more in absolute
    # terms than a naturally stable one (e.g. MPLS), without us having
    # to hardcode volatility per link by hand.
    state.current_latency_ms = _mean_reverting_step(
        state.current_latency_ms, link.baseline_latency_ms,
        volatility=link.baseline_latency_ms * 0.08)

    state.current_jitter_ms = _mean_reverting_step(
        state.current_jitter_ms, link.baseline_jitter_ms,
        volatility=link.baseline_jitter_ms * 0.15)

    state.current_packet_loss_pct = _mean_reverting_step(
        state.current_packet_loss_pct, link.baseline_packet_loss_pct,
        volatility=max(link.baseline_packet_loss_pct * 0.3, 0.01))

    state.current_utilization_pct = _mean_reverting_step(
        state.current_utilization_pct, link.baseline_utilization_pct,
        volatility=link.baseline_utilization_pct * 0.10)
    # Utilization can't sensibly exceed 100%
    state.current_utilization_pct = min(state.current_utilization_pct, 100)

    return {
        "link_id": link.link_id,
        "latency_ms": round(state.current_latency_ms, 2),
        "jitter_ms": round(state.current_jitter_ms, 2),
        "packet_loss_pct": round(state.current_packet_loss_pct, 3),
        "utilization_pct": round(state.current_utilization_pct, 2),
    }


@dataclass
class DeviceState:
    """
    Same idea as LinkState, but for a Device. Tracks live CPU%,
    memory%, and uptime so far for one device across the simulation.
    """
    device: Device
    current_cpu_pct: float = field(init=False)
    current_memory_pct: float = field(init=False)
    uptime_seconds: int = field(init=False, default=0)

    def __post_init__(self):
        self.current_cpu_pct = self.device.baseline_cpu_pct
        self.current_memory_pct = self.device.baseline_memory_pct


def generate_next_device_reading(state: DeviceState, seconds_per_step: int = 10) -> dict:
    """
    Advances a device's state by one time-step and returns the new
    reading as a dict, same shape philosophy as generate_next_reading().

    `seconds_per_step` is how much simulated time passes per call -
    used to grow uptime realistically. Default assumes each call to
    the generator represents 10 seconds of real time passing.
    """
    device = state.device

    state.current_cpu_pct = _mean_reverting_step(
        state.current_cpu_pct, device.baseline_cpu_pct,
        volatility=device.baseline_cpu_pct * 0.12)
    state.current_cpu_pct = min(state.current_cpu_pct, 100)

    state.current_memory_pct = _mean_reverting_step(
        state.current_memory_pct, device.baseline_memory_pct,
        volatility=device.baseline_memory_pct * 0.06)
    state.current_memory_pct = min(state.current_memory_pct, 100)

    # Uptime just keeps climbing under normal conditions - it only
    # resets to 0 if the device reboots, which we'll wire up as part
    # of anomaly injection later. For now it simply grows every step.
    state.uptime_seconds += seconds_per_step

    return {
        "device_id": device.device_id,
        "cpu_pct": round(state.current_cpu_pct, 2),
        "memory_pct": round(state.current_memory_pct, 2),
        "uptime_seconds": state.uptime_seconds,
    }


if __name__ == "__main__":
    # Quick manual test: simulate 10 consecutive readings for the
    # Bangalore MPLS link and print them, so we can visually sanity-check
    # that the numbers wobble gently instead of jumping around randomly.
    test_link = next(l for l in WAN_LINKS if l.link_id == "MPLS-HQ-BLR")
    state = LinkState(test_link)

    print(f"Simulating: {test_link.name}")
    print(f"Baseline -> latency={test_link.baseline_latency_ms}ms, "
          f"jitter={test_link.baseline_jitter_ms}ms, "
          f"loss={test_link.baseline_packet_loss_pct}%, "
          f"util={test_link.baseline_utilization_pct}%\n")

    for i in range(10):
        reading = generate_next_reading(state)
        print(f"t={i:2d}  latency={reading['latency_ms']:6.2f}ms  "
              f"jitter={reading['jitter_ms']:5.2f}ms  "
              f"loss={reading['packet_loss_pct']:5.3f}%  "
              f"util={reading['utilization_pct']:5.2f}%")

    # Same sanity check, now for a device's CPU/memory/uptime
    print()
    test_device = next(d for d in DEVICES if d.device_id == "HQ-CORE-01")
    device_state = DeviceState(test_device)

    print(f"Simulating: {test_device.name}")
    print(f"Baseline -> cpu={test_device.baseline_cpu_pct}%, "
          f"memory={test_device.baseline_memory_pct}%\n")

    for i in range(10):
        reading = generate_next_device_reading(device_state)
        print(f"t={i:2d}  cpu={reading['cpu_pct']:6.2f}%  "
              f"memory={reading['memory_pct']:6.2f}%  "
              f"uptime={reading['uptime_seconds']:4d}s")
