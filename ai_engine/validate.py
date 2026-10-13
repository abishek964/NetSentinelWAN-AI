"""
validate.py — checks whether the model's flagged readings actually
line up with the ground-truth anomaly_events we scheduled ourselves.
"""

import pandas as pd
from db import get_connection
from data_loader import load_readings_by_type
from predict import score_readings


def load_anomaly_events() -> pd.DataFrame:
    query = "SELECT * FROM anomaly_events;"
    with get_connection() as conn:
        df = pd.read_sql(query, conn)
    return df


def assign_steps(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Every link generates exactly one reading per step, in strictly
    increasing time order, no gaps. So we can recover each reading's
    step number just by ranking that link's own readings by time.
    """
    raw = raw.sort_values(["link_id", "reading_time"]).copy()
    raw["step"] = raw.groupby("link_id").cumcount()
    return raw


def is_truly_anomalous(link_id: str, step: int, events: pd.DataFrame) -> bool:
    link_events = events[events["target_id"] == link_id]
    for _, event in link_events.iterrows():
        if event["start_step"] <= step < event["start_step"] + event["duration_steps"]:
            return True
    return False


def validate_link_type(link_type: str, events: pd.DataFrame):
    predictions = score_readings(link_type)
    raw = load_readings_by_type(link_type)
    raw = assign_steps(raw)

    merged = predictions.merge(raw[["reading_id", "link_id", "step"]], on=["reading_id", "link_id"])

    merged["actually_anomalous"] = merged.apply(
        lambda row: is_truly_anomalous(row["link_id"], row["step"], events), axis=1
    )

    true_positives = ((merged["is_anomaly"]) & (merged["actually_anomalous"])).sum()
    false_positives = ((merged["is_anomaly"]) & (~merged["actually_anomalous"])).sum()
    false_negatives = ((~merged["is_anomaly"]) & (merged["actually_anomalous"])).sum()
    true_negatives = ((~merged["is_anomaly"]) & (~merged["actually_anomalous"])).sum()

    print(f"\n--- {link_type} ---")
    print(f"True positives (correctly caught):   {true_positives}")
    print(f"False positives (false alarms):      {false_positives}")
    print(f"False negatives (missed anomalies):  {false_negatives}")
    print(f"True negatives (correctly ignored):  {true_negatives}")


if __name__ == "__main__":
    events = load_anomaly_events()
    for link_type in ["mpls", "ipsec_vpn", "lte_5g_backup"]:
        validate_link_type(link_type, events)