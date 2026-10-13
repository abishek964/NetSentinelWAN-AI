"""
persist.py — runs the trained models and saves every flagged reading,
with its score and explanation, into the anomaly_detections table.
"""

from db import get_connection
from predict import score_and_explain

LINK_TYPES = ["mpls", "ipsec_vpn", "lte_5g_backup"]

INSERT_SQL = """
    INSERT INTO anomaly_detections (reading_id, link_id, anomaly_score, explanation)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (reading_id) DO UPDATE SET
        anomaly_score = EXCLUDED.anomaly_score,
        explanation   = EXCLUDED.explanation,
        detected_at   = now();
"""


def collect_detections() -> list:
    """Runs every model and gathers one tuple per flagged reading."""
    rows = []
    for link_type in LINK_TYPES:
        result = score_and_explain(link_type)
        flagged = result[result["is_anomaly"]]
        for _, r in flagged.iterrows():
            rows.append((
                int(r["reading_id"]),
                r["link_id"],
                float(r["anomaly_score"]),
                r["explanation"],
            ))
    return rows


def main():
    rows = collect_detections()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(INSERT_SQL, rows)
        conn.commit()

    print(f"Saved {len(rows)} detections to anomaly_detections.")


if __name__ == "__main__":
    main()