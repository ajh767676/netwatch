from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip_address = Column(String, index=True)
    device_type = Column(String)

    checks = relationship("Check", back_populates="device")


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    status = Column(String)
    latency_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime)

    device = relationship("Device", back_populates="checks")
