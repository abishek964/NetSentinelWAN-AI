"""
explain.py — explains WHY a reading was flagged, by measuring how far each
of the 4 deviation features sits from "normal" for that link type.
"""

import pandas as pd

FEATURE_COLUMNS = [
    "latency_dev_pct",
    "jitter_dev_pct",
    "packet_loss_dev_pts",
    "utilization_dev_pct",
]

FEATURE_LABELS = {
    "latency_dev_pct": "latency",
    "jitter_dev_pct": "jitter",
    "packet_loss_dev_pts": "packet loss",
    "utilization_dev_pct": "utilization",
}

# A feature counts as a "reason" for the flag if it is at least this many
# spreads away from normal.
REASON_THRESHOLD = 3.0
# Distances beyond this are shown as "more than 100" in the sentence.
DISPLAY_CAP = 100.0

def build_normal_profile(features: pd.DataFrame) -> pd.DataFrame:
    """
    For each feature, work out what "normal" looks like for one link type:
    a typical value (median) and a typical spread (MAD, scaled).
    Median and MAD are used instead of mean and standard deviation because
    the extreme LINK_DOWN readings would inflate the plain average and spread.
    """
    X = features[FEATURE_COLUMNS]
    median = X.median()
    spread = (X - median).abs().median() * 1.4826
    spread = spread.replace(0, 1e-6)  # guard against divide-by-zero
    return pd.DataFrame({"median": median, "spread": spread})


def explain_row(row: pd.Series, profile: pd.DataFrame) -> dict:
    """
    Takes one reading's feature values and the normal profile, and returns
    per-feature distances (in spreads) plus a plain-English summary.
    """
    distances = (row[FEATURE_COLUMNS] - profile["median"]) / profile["spread"]
    ranked = distances.reindex(distances.abs().sort_values(ascending=False).index)

    reasons = [f for f in ranked.index if abs(ranked[f]) >= REASON_THRESHOLD]
    if not reasons:
        reasons = [ranked.index[0]]  # always name at least the biggest one

    parts = []
    for f in reasons:
        direction = "above" if ranked[f] > 0 else "below"
        magnitude = abs(ranked[f])
        if magnitude > DISPLAY_CAP:
            amount = f"more than {DISPLAY_CAP:,.0f}"
        else:
            amount = f"{magnitude:,.1f}"
        parts.append(f"{FEATURE_LABELS[f]} is {amount} spreads {direction} normal")

    return {
        "distances": ranked.to_dict(),
        "summary": "; ".join(parts),
    }


if __name__ == "__main__":
    from data_loader import load_readings_by_type
    from feature_engineering import compute_deviation_features
    from predict import score_readings

    link_type = "mpls"
    raw = load_readings_by_type(link_type)
    features = compute_deviation_features(raw)
    profile = build_normal_profile(features)

    predictions = score_readings(link_type)
    merged = features.merge(predictions, on=["reading_id", "link_id"])

    flagged = merged[merged["is_anomaly"]].sort_values("anomaly_score").head(8)
    for _, row in flagged.iterrows():
        result = explain_row(row, profile)
        print(f"{row['link_id']} (reading {row['reading_id']}): {result['summary']}")