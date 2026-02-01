"""
Health Record Model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Record details
    record_type = Column(String(50))  # consultation, lab_result, prescription, imaging
    record_date = Column(DateTime(timezone=True), server_default=func.now())
    title = Column(String(255))
    description = Column(Text)
    
    # Vital signs (optional)
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)
    heart_rate = Column(Integer)
    temperature = Column(Float)
    weight = Column(Float)
    height = Column(Float)
    
    # Files
    file_url = Column(String(500))
    file_type = Column(String(50))
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="health_records")
