from pydantic import BaseModel


class AnomalyEventOut(BaseModel):
    event_id: str
    anomaly_type: str
    target_id: str
    start_step: int
    duration_steps: int
    severity: float
