from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    sites,
    devices,
    wan_links,
    link_readings,
    device_readings,
    anomaly_events,
    anomaly_detections,
)

app = FastAPI(title="NetSentinelWAN AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sites.router)
app.include_router(devices.router)
app.include_router(wan_links.router)
app.include_router(link_readings.router)
app.include_router(device_readings.router)
app.include_router(anomaly_events.router)
app.include_router(anomaly_detections.router)

@app.get("/")
def root():
    return {"status": "NetSentinelWAN AI API is running"}
