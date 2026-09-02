from pydantic import BaseModel


class DeviceOut(BaseModel):
    device_id: str
    device_name: str
    site_id: int
    role: str
    baseline_cpu_pct: float
    baseline_memory_pct: float
