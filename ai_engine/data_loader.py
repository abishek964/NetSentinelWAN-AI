"""
data_loader.py — pulls WAN link readings from Postgres into a pandas DataFrame,
joined with link_type and baseline values from wan_links.
"""

import pandas as pd
from db import get_connection


def load_readings() -> pd.DataFrame:
    """
    Loads all link_readings, joined with wan_links to attach link_type
    and baseline_* columns to every row.

    Returns a pandas DataFrame with one row per reading.
    """
    query = """
        SELECT
            lr.reading_id,
            lr.link_id,
            lr.reading_time,
            lr.latency_ms,
            lr.jitter_ms,
            lr.packet_loss_pct,
            lr.utilization_pct,
            wl.link_type,
            wl.baseline_latency_ms,
            wl.baseline_jitter_ms,
            wl.baseline_packet_loss_pct,
            wl.baseline_utilization_pct
        FROM link_readings lr
        JOIN wan_links wl ON lr.link_id = wl.link_id
        ORDER BY lr.reading_time;
    """

    with get_connection() as conn:
        df = pd.read_sql(query, conn)

    return df


def load_readings_by_type(link_type: str) -> pd.DataFrame:
    """
    Convenience filter: returns only the readings belonging to one link_type
    (e.g. 'mpls', 'ipsec_vpn', 'lte_5g_backup'). This is what train.py will
    call once per type, to train one model per link_type.
    """
    df = load_readings()
    return df[df["link_type"] == link_type].reset_index(drop=True)

if __name__ == "__main__":
    df = load_readings()
    print(df.shape)
    print(df.head())

    for t in ["mpls", "ipsec_vpn", "lte_5g_backup"]:
        subset = load_readings_by_type(t)
        print(f"{t}: {subset.shape[0]} readings")