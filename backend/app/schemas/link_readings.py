from datetime import datetime

from pydantic import BaseModel


class LinkReadingOut(BaseModel):
    reading_id: int
    link_id: str
    reading_time: datetime
    latency_ms: float
    jitter_ms: float
    packet_loss_pct: float
    utilization_pct: float
