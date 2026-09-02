from datetime import datetime

from pydantic import BaseModel


class DeviceReadingOut(BaseModel):
    reading_id: int
    device_id: str
    reading_time: datetime
    cpu_pct: float
    memory_pct: float
