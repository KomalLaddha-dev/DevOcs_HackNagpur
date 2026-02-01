"""
Doctor Model
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    specialty = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True)
    experience_years = Column(Integer)
    qualification = Column(String(255))
    bio = Column(Text)
    consultation_fee = Column(Float)
    is_available = Column(Boolean, default=True)
    max_patients_per_day = Column(Integer, default=30)
    current_patient_count = Column(Integer, default=0)
    room_number = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")
    schedules = relationship("DoctorSchedule", back_populates="doctor")


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time = Column(String(10))  # "09:00"
    end_time = Column(String(10))    # "17:00"
    is_active = Column(Boolean, default=True)

    doctor = relationship("Doctor", back_populates="schedules")
