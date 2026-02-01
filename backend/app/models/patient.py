"""
Patient Model
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    date_of_birth = Column(Date)
    gender = Column(String(20))
    blood_group = Column(String(10))
    address = Column(Text)
    emergency_contact = Column(String(20))
    medical_history = Column(Text)
    allergies = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="patient_profile")
    appointments = relationship("Appointment", back_populates="patient")
    health_records = relationship("HealthRecord", back_populates="patient")
