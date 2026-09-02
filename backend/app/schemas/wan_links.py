from pydantic import BaseModel


class WanLinkOut(BaseModel):
    link_id: str
    link_name: str
    site_a_id: int
    site_b_id: int
    link_type: str
    baseline_latency_ms: float
    baseline_jitter_ms: float
    baseline_packet_loss_pct: float
    baseline_utilization_pct: float
