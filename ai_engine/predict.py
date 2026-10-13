"""
predict.py — loads each trained model and scores readings as
normal/anomalous. No explanation logic yet (that's explain.py, later).
"""

import joblib
import pandas as pd

from data_loader import load_readings_by_type
from feature_engineering import compute_deviation_features
from explain import build_normal_profile, explain_row

FEATURE_COLUMNS = [
    "latency_dev_pct",
    "jitter_dev_pct",
    "packet_loss_dev_pts",
    "utilization_dev_pct",
]


def score_readings(link_type: str) -> pd.DataFrame:
    """
    Loads the saved model for this link_type, scores all its readings,
    and returns a DataFrame with reading_id, link_id, is_anomaly, and
    a raw anomaly_score.
    """
    model = joblib.load(f"models/{link_type}_model.pkl")

    raw = load_readings_by_type(link_type)
    features = compute_deviation_features(raw)
    X = features[FEATURE_COLUMNS]

    # sklearn's convention: predict() returns -1 for anomalies, 1 for normal
    predictions = model.predict(X)
    scores = model.decision_function(X)

    result = features[["reading_id", "link_id"]].copy()
    result["is_anomaly"] = predictions == -1
    result["anomaly_score"] = scores

    return result

def score_and_explain(link_type: str) -> pd.DataFrame:
    """
    Like score_readings, but also attaches a plain-English explanation
    to every reading the model flagged. Normal readings get no explanation.
    """
    model = joblib.load(f"models/{link_type}_model.pkl")

    raw = load_readings_by_type(link_type)
    features = compute_deviation_features(raw)
    X = features[FEATURE_COLUMNS]
    profile = build_normal_profile(features)

    result = features[["reading_id", "link_id"]].copy()
    result["is_anomaly"] = model.predict(X) == -1
    result["anomaly_score"] = model.decision_function(X)
    result["explanation"] = None

    for idx in result.index[result["is_anomaly"]]:
        summary = explain_row(features.loc[idx], profile)["summary"]
        result.at[idx, "explanation"] = summary

    return result

if __name__ == "__main__":
    for link_type in ["mpls", "ipsec_vpn", "lte_5g_backup"]:
        result = score_and_explain(link_type)
        flagged = result[result["is_anomaly"]]
        print(f"\n{link_type}: {len(flagged)}/{len(result)} flagged")
        print(flagged.sort_values("anomaly_score").head(2)[["link_id", "explanation"]].to_string())