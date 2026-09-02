from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.database import get_db
from app.schemas.sites import SiteOut

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteOut])
def list_sites(conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT site_id, site_name FROM sites ORDER BY site_id;")
        rows = cur.fetchall()
    return rows


@router.get("/{site_id}", response_model=SiteOut)
def get_site(site_id: int, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT site_id, site_name FROM sites WHERE site_id = %s;", (site_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    return row
