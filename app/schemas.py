from pydantic import BaseModel
from datetime import datetime

class DeviceBase(BaseModel):
    name: str
    ip_address: str
    device_type: str

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int

    class Config:
        orm_mode = True


class CheckBase(BaseModel):
    device_id: int
    status: str
    latency_ms: float | None = None

class Check(CheckBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
