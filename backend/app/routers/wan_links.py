from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.database import get_db
from app.schemas.wan_links import WanLinkOut

router = APIRouter(prefix="/wan_links", tags=["wan_links"])

BASE_SELECT = """
    SELECT link_id, link_name, site_a_id, site_b_id, link_type,
           baseline_latency_ms, baseline_jitter_ms,
           baseline_packet_loss_pct, baseline_utilization_pct
    FROM wan_links
"""


@router.get("", response_model=list[WanLinkOut])
def list_wan_links(site_id: Optional[int] = None, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        if site_id is not None:
            # a link touches a site if it's on EITHER end (site_a or site_b)
            cur.execute(
                BASE_SELECT + " WHERE site_a_id = %s OR site_b_id = %s ORDER BY link_id;",
                (site_id, site_id),
            )
        else:
            cur.execute(BASE_SELECT + " ORDER BY link_id;")
        rows = cur.fetchall()
    return rows


@router.get("/{link_id}", response_model=WanLinkOut)
def get_wan_link(link_id: str, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(BASE_SELECT + " WHERE link_id = %s;", (link_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"WAN link {link_id} not found")
    return row
