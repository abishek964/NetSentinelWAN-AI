"""
feature_engineering.py — converts raw readings + baselines into
percentage-deviation features, ready to feed into the Isolation Forest.
"""

import numpy as np
import pandas as pd
from data_loader import load_readings_by_type


def compute_deviation_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds percentage-deviation features:
        (actual_reading - baseline) / baseline * 100

    Returns a NEW DataFrame with just the feature columns (plus IDs for
    traceability) — does not modify the input df.
    """
    # Guard against a baseline of exactly 0, which would cause a
    # divide-by-zero (producing inf or NaN). Replace any zero baseline
    # with a tiny number instead, so the math stays well-behaved.
    safe_baseline_latency = df["baseline_latency_ms"].replace(0, 1e-6)
    safe_baseline_jitter = df["baseline_jitter_ms"].replace(0, 1e-6)
    safe_baseline_loss = df["baseline_packet_loss_pct"].replace(0, 1e-6)
    safe_baseline_util = df["baseline_utilization_pct"].replace(0, 1e-6)

    features = pd.DataFrame()
    features["reading_id"] = df["reading_id"]
    features["link_id"] = df["link_id"]

    features["latency_dev_pct"] = (
        (df["latency_ms"] - df["baseline_latency_ms"]) / safe_baseline_latency * 100
    )
    features["jitter_dev_pct"] = (
        (df["jitter_ms"] - df["baseline_jitter_ms"]) / safe_baseline_jitter * 100
    )
    features["packet_loss_dev_pts"] = (
        df["packet_loss_pct"] - df["baseline_packet_loss_pct"]
    )
    features["utilization_dev_pct"] = (
        (df["utilization_pct"] - df["baseline_utilization_pct"]) / safe_baseline_util * 100
    )

    return features


if __name__ == "__main__":
    for link_type in ["mpls", "ipsec_vpn", "lte_5g_backup"]:
        raw = load_readings_by_type(link_type)
        features = compute_deviation_features(raw)
        print(f"\n--- {link_type} ---")
        print(features.describe())