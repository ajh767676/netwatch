from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, SessionLocal
from ping3 import ping
from datetime import datetime


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NetWatch Dashboard")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_ping_check(db: Session):
    devices = db.query(models.Device).all()

    for d in devices:
        latency = ping(d.ip_address, timeout=2)

        if latency is None:
            status = "Offline"
            latency_ms = None
        else:
            status = "Online"
            latency_ms = latency * 1000  # convert seconds → ms

        check = models.Check(
            device_id=d.id,
            status=status,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow()
        )

        db.add(check)

    db.commit()


@app.post("/devices", response_model=schemas.Device)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    db_device = models.Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@app.get("/devices", response_model=list[schemas.Device])
def list_devices(db: Session = Depends(get_db)):
    return db.query(models.Device).all()

@app.post("/status/run")
def run_status_check(db: Session = Depends(get_db)):
    run_ping_check(db)
    return {"detail": "Ping checks completed"}

@app.get("/status")
def get_latest_status(db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    result = []

    for d in devices:
        latest = (
            db.query(models.Check)
            .filter(models.Check.device_id == d.id)
            .order_by(models.Check.timestamp.desc())
            .first()
        )

        if latest:
            result.append({
                "device": d.name,
                "ip": d.ip_address,
                "status": latest.status,
                "latency_ms": latest.latency_ms,
                "timestamp": latest.timestamp
            })

    return result

@app.get("/history")
def get_history(device_id: int, db: Session = Depends(get_db)):
    checks = (
        db.query(models.Check)
        .filter(models.Check.device_id == device_id)
        .order_by(models.Check.timestamp.asc())
        .all()
    )
    return checks

def calculate_uptime(checks):
    if not checks:
        return 0.0

    total = len(checks)
    online = sum(1 for c in checks if c.status == "Online")

    return round((online / total) * 100, 2)

def calculate_average_latency(checks):
    latencies = [c.latency_ms for c in checks if c.latency_ms is not None]

    if not latencies:
        return None

    return round(sum(latencies) / len(latencies), 2)

@app.get("/stats")
def get_stats(device_id: int, db: Session = Depends(get_db)):
    checks = (
        db.query(models.Check)
        .filter(models.Check.device_id == device_id)
        .order_by(models.Check.timestamp.asc())
        .all()
    )

    if not checks:
        return {"detail": "No history for this device"}

    uptime = calculate_uptime(checks)
    avg_latency = calculate_average_latency(checks)
    last = checks[-1]

    return {
        "device_id": device_id,
        "uptime_percent": uptime,
        "average_latency_ms": avg_latency,
        "last_status": last.status,
        "last_latency_ms": last.latency_ms,
        "last_timestamp": last.timestamp,
        "total_checks": len(checks)
    }
