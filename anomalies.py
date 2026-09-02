"""
anomalies.py

Defines SCHEDULED anomalies: events where a link or device temporarily
behaves abnormally (a link degrading, a device rebooting, a CPU spike).

Why this matters for the project: without this file, our simulator only
ever produces "healthy" data wobbling gently around baselines forever.
An anomaly detection AI model needs to see actual bad patterns during
training/testing - this file is what creates those patterns on purpose,
on a schedule we control.

DESIGN CHOICE: rather than rewriting the existing generator functions,
we generate a NORMAL reading first (using the code we already built),
then run it through an "apply_anomaly" function that adjusts the
numbers afterward, only if an anomaly is currently active. This keeps
the original generator functions untouched and simple.
"""

from dataclasses import dataclass
from enum import Enum


class AnomalyType(Enum):
    LINK_DEGRADATION = "link_degradation"   # latency/jitter/loss climb temporarily
    LINK_DOWN = "link_down"                  # link effectively fails
    DEVICE_CPU_SPIKE = "device_cpu_spike"
    DEVICE_REBOOT = "device_reboot"          # uptime resets, brief low CPU


@dataclass
class AnomalyEvent:
    """
    Describes ONE scheduled anomaly: what it affects, when it starts,
    how long it lasts, and how severe it is.
    """
    event_id: str
    anomaly_type: AnomalyType
    target_id: str          # a link_id or device_id, depending on type
    start_step: int         # which simulation step this begins at
    duration_steps: int     # how many steps it lasts
    severity: float = 2.5   # multiplier - how much worse than normal at peak

    def is_active_at(self, step: int) -> bool:
        """True if this anomaly is currently happening at the given step."""
        return self.start_step <= step < self.start_step + self.duration_steps

    def progress_at(self, step: int) -> float:
        """
        Returns a value from 0.0 to 1.0 to 0.0 describing HOW SEVERE the
        anomaly is right now - it ramps up, peaks in the middle, then
        ramps back down. This is what makes it look like a real gradual
        degradation and recovery, instead of an instant on/off switch.

        Example with duration_steps=10:
          step 0 (start):  progress = 0.0   (just beginning)
          step 5 (middle): progress = 1.0   (worst point)
          step 9 (end):    progress ~ 0.2   (almost recovered)
        """
        if not self.is_active_at(step):
            return 0.0
        elapsed = step - self.start_step
        halfway = self.duration_steps / 2
        if elapsed <= halfway:
            return elapsed / halfway if halfway > 0 else 1.0
        else:
            return (self.duration_steps - elapsed) / halfway


def apply_link_anomaly(reading: dict, event: AnomalyEvent, step: int) -> dict:
    """
    Takes a NORMAL link reading (already generated) and, if this event
    is currently active for this link, pushes the numbers toward
    unhealthy values. Returns the reading unchanged if nothing's active.
    """
    progress = event.progress_at(step)
    if progress == 0.0:
        return reading  # anomaly not active right now - leave reading as-is

    extra_severity = (event.severity - 1) * progress

    if event.anomaly_type == AnomalyType.LINK_DEGRADATION:
        reading["latency_ms"] = round(reading["latency_ms"] * (1 + extra_severity), 2)
        reading["jitter_ms"] = round(reading["jitter_ms"] * (1 + extra_severity), 2)
        reading["packet_loss_pct"] = round(
            reading["packet_loss_pct"] * (1 + extra_severity * 3), 3)

    elif event.anomaly_type == AnomalyType.LINK_DOWN:
        # A fully down link: near-total loss, huge latency, no useful traffic
        reading["latency_ms"] = 9999.0
        reading["packet_loss_pct"] = 100.0
        reading["utilization_pct"] = 0.0

    return reading


def apply_device_anomaly(reading: dict, event: AnomalyEvent, step: int,
                          device_state) -> dict:
    """
    Same idea as apply_link_anomaly, but for device readings (CPU/uptime).
    Takes device_state too, because a reboot needs to reset uptime_seconds
    on the actual state object, not just in the returned reading.
    """
    progress = event.progress_at(step)
    if progress == 0.0:
        return reading

    if event.anomaly_type == AnomalyType.DEVICE_CPU_SPIKE:
        extra_severity = (event.severity - 1) * progress
        reading["cpu_pct"] = round(min(reading["cpu_pct"] * (1 + extra_severity), 100), 2)

    elif event.anomaly_type == AnomalyType.DEVICE_REBOOT:
        if step == event.start_step:
            device_state.uptime_seconds = 0
        reading["uptime_seconds"] = device_state.uptime_seconds
        reading["cpu_pct"] = 5.0  # devices run near-idle CPU while rebooting

    return reading


if __name__ == "__main__":
    # Quick manual test: schedule ONE link degradation event and print
    # readings across a range of steps to see the before/during/after shape.
    from topology import WAN_LINKS
    from telemetry_generator import LinkState, generate_next_reading

    test_link = next(l for l in WAN_LINKS if l.link_id == "MPLS-HQ-BLR")
    state = LinkState(test_link)

    # Schedule: this link degrades starting at step 5, for 8 steps total
    scheduled_event = AnomalyEvent(
        event_id="EVT-001",
        anomaly_type=AnomalyType.LINK_DEGRADATION,
        target_id=test_link.link_id,
        start_step=5,
        duration_steps=8,
        severity=3.0,
    )

    print(f"Simulating: {test_link.name}")
    print(f"Anomaly scheduled: steps 5-12 (degradation)\n")

    for step in range(18):
        reading = generate_next_reading(state)
        reading = apply_link_anomaly(reading, scheduled_event, step)

        flag = "  <-- ANOMALY" if scheduled_event.is_active_at(step) else ""
        print(f"step={step:2d}  latency={reading['latency_ms']:7.2f}ms  "
              f"loss={reading['packet_loss_pct']:6.3f}%{flag}")
