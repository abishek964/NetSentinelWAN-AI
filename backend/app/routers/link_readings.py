from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.database import get_db
from app.schemas.link_readings import LinkReadingOut

router = APIRouter(prefix="/link_readings", tags=["link_readings"])

BASE_SELECT = """
    SELECT reading_id, link_id, reading_time,
           latency_ms, jitter_ms, packet_loss_pct, utilization_pct
    FROM link_readings
"""


@router.get("", response_model=list[LinkReadingOut])
def list_link_readings(
    link_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    conn: Connection = Depends(get_db),
):
    # Build the WHERE clause piece by piece, only adding conditions
    # for filters the caller actually provided.
    conditions = []
    params = []

    if link_id is not None:
        conditions.append("link_id = %s")
        params.append(link_id)
    if start_time is not None:
        conditions.append("reading_time >= %s")
        params.append(start_time)
    if end_time is not None:
        conditions.append("reading_time <= %s")
        params.append(end_time)

    query = BASE_SELECT
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY reading_time DESC LIMIT %s;"
    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return rows


@router.get("/{reading_id}", response_model=LinkReadingOut)
def get_link_reading(reading_id: int, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(BASE_SELECT + " WHERE reading_id = %s;", (reading_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Link reading {reading_id} not found")
    return row
