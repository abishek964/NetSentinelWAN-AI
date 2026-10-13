"""
populate_readings.py

telemetry_generator.py only COMPUTES fluctuating values - it never
talks to the database. This script is the missing piece: it loops
that generator forward in simulated time, for every link and every
device, and writes each resulting reading into Neon.

Run this from the project root (same folder as topology.py,
telemetry_generator.py, anomalies.py) - NOT from inside backend/.
"""

from datetime import datetime, timedelta

import psycopg

from anomalies import AnomalyEvent, AnomalyType, apply_link_anomaly

from topology import WAN_LINKS, DEVICES
from telemetry_generator import (
    LinkState,
    DeviceState,
    generate_next_reading,
    generate_next_device_reading,
)

# --- Config: tweak these if you want more/less data later ---
NUM_STEPS = 200          # how many readings to generate per link/device
SECONDS_PER_STEP = 10    # how much simulated time passes between readings

ANOMALY_SCHEDULE = [
AnomalyEvent("EVT-001", AnomalyType.LINK_DEGRADATION, "MPLS-HQ-BLR", start_step=40,  duration_steps=14, severity=2.5),
AnomalyEvent("EVT-002", AnomalyType.LINK_DEGRADATION, "MPLS-HQ-HYD", start_step=100, duration_steps=16, severity=3.0),
AnomalyEvent("EVT-003", AnomalyType.LINK_DOWN,        "MPLS-HQ-MUM", start_step=150, duration_steps=6,  severity=2.5),
AnomalyEvent("EVT-004", AnomalyType.LINK_DEGRADATION, "MPLS-HQ-DEL", start_step=170, duration_steps=10, severity=2.0),

AnomalyEvent("EVT-005", AnomalyType.LINK_DEGRADATION, "VPN-HQ-BLR",  start_step=30,  duration_steps=12, severity=2.5),
AnomalyEvent("EVT-006", AnomalyType.LINK_DEGRADATION, "VPN-HQ-HYD",  start_step=90,  duration_steps=15, severity=3.0),
AnomalyEvent("EVT-007", AnomalyType.LINK_DOWN,        "VPN-HQ-MUM",  start_step=140, duration_steps=5,  severity=2.5),
AnomalyEvent("EVT-008", AnomalyType.LINK_DEGRADATION, "VPN-HQ-DEL",  start_step=175, duration_steps=10, severity=2.0),

AnomalyEvent("EVT-009", AnomalyType.LINK_DEGRADATION, "LTE-HQ-DEL",  start_step=50,  duration_steps=12, severity=2.5),
AnomalyEvent("EVT-010", AnomalyType.LINK_DOWN,        "LTE-HQ-DEL",  start_step=140, duration_steps=4,  severity=2.5),
]

def load_database_url(env_path: str = "backend/.env") -> str:
    """
    Reads DATABASE_URL straight out of backend/.env, the same file
    FastAPI's config.py uses - so there's only one place your Neon
    connection string ever lives.
    """
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1]
    raise RuntimeError(f"DATABASE_URL not found in {env_path}")


def main():
    database_url = load_database_url()

    # One State object per link/device, tracking its "current" value
    # so each new reading nudges forward from the last one instead of
    # starting fresh every time (this is exactly what LinkState/DeviceState
    # are for in telemetry_generator.py).
    link_states = [LinkState(link) for link in WAN_LINKS]
    device_states = [DeviceState(device) for device in DEVICES]

    # Start far enough in the past that the LAST reading lands close
    # to right now - gives you a realistic, recent time window to
    # query against once it's in the database.
    start_time = datetime.utcnow() - timedelta(seconds=NUM_STEPS * SECONDS_PER_STEP)

    link_rows = []
    device_rows = []

    for step in range(NUM_STEPS):
        reading_time = start_time + timedelta(seconds=step * SECONDS_PER_STEP)

        for state in link_states:
            r = generate_next_reading(state)

    # Apply any anomaly currently active for THIS link at THIS step
            for event in ANOMALY_SCHEDULE:
                if event.target_id == r["link_id"] and event.is_active_at(step):
                    r = apply_link_anomaly(r, event, step)

            link_rows.append((
                        r["link_id"],
                        reading_time,
                        r["latency_ms"],
                        r["jitter_ms"],
                        r["packet_loss_pct"],
                        r["utilization_pct"],
                    ))

        for state in device_states:
            r = generate_next_device_reading(state, seconds_per_step=SECONDS_PER_STEP)
            device_rows.append((
                r["device_id"],
                reading_time,
                r["cpu_pct"],
                r["memory_pct"],
            ))

    print(f"Generated {len(link_rows)} link readings across {len(link_states)} links.")
    print(f"Generated {len(device_rows)} device readings across {len(device_states)} devices.")
    print("Connecting to Neon and inserting...")

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            # executemany runs the same INSERT once per row in the list -
            # much faster than looping and calling execute() one row at a
            # time, since psycopg batches them efficiently.
            cur.executemany(
                """
                INSERT INTO link_readings
                    (link_id, reading_time, latency_ms, jitter_ms,
                     packet_loss_pct, utilization_pct)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                link_rows,
            )
            cur.executemany(
                """
                INSERT INTO device_readings
                    (device_id, reading_time, cpu_pct, memory_pct)
                VALUES (%s, %s, %s, %s);
                """,
                device_rows,
            )
            anomaly_event_rows = [
                (e.event_id, e.anomaly_type.value, e.target_id, e.start_step, e.duration_steps, e.severity)
                for e in ANOMALY_SCHEDULE
            ]
            cur.executemany(
                """
                INSERT INTO anomaly_events
                    (event_id, anomaly_type, target_id, start_step, duration_steps, severity)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                anomaly_event_rows,
            )
        conn.commit()

    print("Done - data committed to Neon.")


if __name__ == "__main__":
    main()
