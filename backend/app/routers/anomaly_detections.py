from typing import Optional

from fastapi import APIRouter, Depends
from psycopg import Connection

from app.database import get_db
from app.schemas.anomaly_detections import AnomalyDetectionOut, LinkSummaryOut

router = APIRouter(prefix="/anomaly_detections", tags=["anomaly_detections"])


@router.get("", response_model=list[AnomalyDetectionOut])
def list_detections(
    link_id: Optional[str] = None,
    limit: int = 100,
    conn: Connection = Depends(get_db),
):
    query = """
        SELECT d.detection_id, d.reading_id, d.link_id, d.anomaly_score,
               d.explanation, d.detected_at,
               r.reading_time, r.latency_ms, r.jitter_ms,
               r.packet_loss_pct, r.utilization_pct
        FROM anomaly_detections d
        JOIN link_readings r ON r.reading_id = d.reading_id
    """
    params = []
    if link_id is not None:
        query += " WHERE d.link_id = %s"
        params.append(link_id)
    query += " ORDER BY r.reading_time DESC LIMIT %s;"
    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.get("/summary", response_model=list[LinkSummaryOut])
def link_summary(conn: Connection = Depends(get_db)):
    query = """
        SELECT l.link_id,
               COALESCE(c.anomaly_count, 0) AS anomaly_count,
               lr.reading_time AS latest_reading_time,
               lr.latency_ms AS latest_latency_ms,
               lr.packet_loss_pct AS latest_packet_loss_pct,
               lr.utilization_pct AS latest_utilization_pct,
               ld.anomaly_score AS latest_anomaly_score
        FROM wan_links l
        LEFT JOIN (
            SELECT link_id, COUNT(*) AS anomaly_count
            FROM anomaly_detections GROUP BY link_id
        ) c ON c.link_id = l.link_id
        LEFT JOIN LATERAL (
            SELECT reading_id, reading_time, latency_ms,
                   packet_loss_pct, utilization_pct
            FROM link_readings
            WHERE link_id = l.link_id
            ORDER BY reading_time DESC LIMIT 1
        ) lr ON TRUE
        LEFT JOIN anomaly_detections ld ON ld.reading_id = lr.reading_id
        ORDER BY l.link_id;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()