"""
Queue Entry Model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    
    # Queue specific fields
    token_number = Column(String(20), unique=True)
    check_in_time = Column(DateTime(timezone=True), server_default=func.now())
    called_time = Column(DateTime(timezone=True), nullable=True)
    completed_time = Column(DateTime(timezone=True), nullable=True)
    
    # Priority calculation
    triage_score = Column(Integer, default=1)  # 1-5 (5 = most urgent)
    wait_time_minutes = Column(Integer, default=0)
    age_factor = Column(Float, default=1.0)
    chronic_condition_factor = Column(Float, default=1.0)
    priority_score = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default="waiting")  # waiting, called, in_consultation, completed
    is_emergency = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient")
    appointment = relationship("Appointment")
    doctor = relationship("Doctor")
