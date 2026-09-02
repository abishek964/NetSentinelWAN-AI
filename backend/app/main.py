from fastapi import FastAPI

from app.routers import (
    sites,
    devices,
    wan_links,
    link_readings,
    device_readings,
    anomaly_events,
)

app = FastAPI(title="NetSentinelWAN AI API")

app.include_router(sites.router)
app.include_router(devices.router)
app.include_router(wan_links.router)
app.include_router(link_readings.router)
app.include_router(device_readings.router)
app.include_router(anomaly_events.router)


@app.get("/")
def root():
    return {"status": "NetSentinelWAN AI API is running"}
