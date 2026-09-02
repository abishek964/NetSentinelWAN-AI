from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.database import get_db
from app.schemas.device_readings import DeviceReadingOut

router = APIRouter(prefix="/device_readings", tags=["device_readings"])

BASE_SELECT = """
    SELECT reading_id, device_id, reading_time, cpu_pct, memory_pct
    FROM device_readings
"""


@router.get("", response_model=list[DeviceReadingOut])
def list_device_readings(
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    conn: Connection = Depends(get_db),
):
    conditions = []
    params = []

    if device_id is not None:
        conditions.append("device_id = %s")
        params.append(device_id)
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


@router.get("/{reading_id}", response_model=DeviceReadingOut)
def get_device_reading(reading_id: int, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(BASE_SELECT + " WHERE reading_id = %s;", (reading_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Device reading {reading_id} not found")
    return row
