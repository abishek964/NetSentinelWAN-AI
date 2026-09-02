from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.database import get_db
from app.schemas.anomaly_events import AnomalyEventOut

router = APIRouter(prefix="/anomaly_events", tags=["anomaly_events"])

BASE_SELECT = """
    SELECT event_id, anomaly_type, target_id, start_step, duration_steps, severity
    FROM anomaly_events
"""


@router.get("", response_model=list[AnomalyEventOut])
def list_anomaly_events(
    anomaly_type: Optional[str] = None,
    target_id: Optional[str] = None,
    conn: Connection = Depends(get_db),
):
    conditions = []
    params = []

    if anomaly_type is not None:
        conditions.append("anomaly_type = %s")
        params.append(anomaly_type)
    if target_id is not None:
        conditions.append("target_id = %s")
        params.append(target_id)

    query = BASE_SELECT
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY start_step DESC;"

    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return rows


@router.get("/{event_id}", response_model=AnomalyEventOut)
def get_anomaly_event(event_id: str, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(BASE_SELECT + " WHERE event_id = %s;", (event_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Anomaly event {event_id} not found")
    return row
