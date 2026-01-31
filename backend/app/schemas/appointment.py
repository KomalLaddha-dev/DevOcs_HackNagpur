"""
Appointment Schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    doctor_id: int
    scheduled_time: datetime
    appointment_type: str = "in_person"
    symptoms: Optional[str] = None


class AppointmentUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    status: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    scheduled_time: datetime
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    status: str
    appointment_type: str
    symptoms: Optional[str]
    triage_score: Optional[int]
    diagnosis: Optional[str]
    prescription: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
