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
        conn.commit()

    print("Done - data committed to Neon.")


if __name__ == "__main__":
    main()
