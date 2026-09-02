from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.database import get_db
from app.schemas.devices import DeviceOut

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(site_id: Optional[int] = None, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        if site_id is not None:
            cur.execute(
                """
                SELECT device_id, device_name, site_id, role,
                       baseline_cpu_pct, baseline_memory_pct
                FROM devices
                WHERE site_id = %s
                ORDER BY device_id;
                """,
                (site_id,),
            )
        else:
            cur.execute(
                """
                SELECT device_id, device_name, site_id, role,
                       baseline_cpu_pct, baseline_memory_pct
                FROM devices
                ORDER BY device_id;
                """
            )
        rows = cur.fetchall()
    return rows


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: str, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT device_id, device_name, site_id, role,
                   baseline_cpu_pct, baseline_memory_pct
            FROM devices
            WHERE device_id = %s;
            """,
            (device_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return row
