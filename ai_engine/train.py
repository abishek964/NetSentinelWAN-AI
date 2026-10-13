"""
train.py — trains one Isolation Forest per link_type, using the known
contamination rate from our scheduled anomalies, and saves each model
to disk with joblib.
"""

import joblib
from sklearn.ensemble import IsolationForest

from data_loader import load_readings_by_type
from feature_engineering import compute_deviation_features

# Exact contamination per type, computed from ANOMALY_SCHEDULE in
# populate_readings.py (anomalous steps / total readings per type).
CONTAMINATION_BY_TYPE = {
    "mpls": 0.0575,
    "ipsec_vpn": 0.0525,
    "lte_5g_backup": 0.08,
}

FEATURE_COLUMNS = [
    "latency_dev_pct",
    "jitter_dev_pct",
    "packet_loss_dev_pts",
    "utilization_dev_pct",
]


def train_model_for_type(link_type: str):
    raw = load_readings_by_type(link_type)
    features = compute_deviation_features(raw)

    # The model should only ever see the 4 numeric deviation columns —
    # reading_id and link_id are for OUR traceability, not model input.
    X = features[FEATURE_COLUMNS]

    model = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION_BY_TYPE[link_type],
        random_state=42,
    )
    model.fit(X)

    model_path = f"models/{link_type}_model.pkl"
    joblib.dump(model, model_path)
    print(f"Trained and saved: {model_path}")

    return model


if __name__ == "__main__":
    for link_type in CONTAMINATION_BY_TYPE:
        train_model_for_type(link_type)