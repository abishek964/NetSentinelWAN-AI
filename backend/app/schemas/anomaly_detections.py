from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AnomalyDetectionOut(BaseModel):
    detection_id: int
    reading_id: int
    link_id: str
    anomaly_score: float
    explanation: str
    detected_at: datetime
    reading_time: datetime
    latency_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    packet_loss_pct: Optional[float] = None
    utilization_pct: Optional[float] = None


class LinkSummaryOut(BaseModel):
    link_id: str
    anomaly_count: int
    latest_reading_time: Optional[datetime] = None
    latest_latency_ms: Optional[float] = None
    latest_packet_loss_pct: Optional[float] = None
    latest_utilization_pct: Optional[float] = None
    latest_anomaly_score: Optional[float] = None