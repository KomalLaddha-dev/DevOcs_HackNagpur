"""
Doctor Schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DoctorCreate(BaseModel):
    specialty: str
    license_number: str
    experience_years: Optional[int] = None
    qualification: Optional[str] = None
    bio: Optional[str] = None
    consultation_fee: Optional[float] = None
    max_patients_per_day: int = 30
    room_number: Optional[str] = None


class DoctorResponse(BaseModel):
    id: int
    user_id: int
    specialty: str
    license_number: str
    experience_years: Optional[int]
    qualification: Optional[str]
    is_available: bool
    consultation_fee: Optional[float]
    room_number: Optional[str]
    current_patient_count: int
    max_patients_per_day: int

    class Config:
        from_attributes = True


class AvailabilityUpdate(BaseModel):
    is_available: bool
    reason: Optional[str] = None


class ScheduleSlot(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    is_active: bool = True


class DoctorSchedule(BaseModel):
    doctor_id: int
    slots: List[ScheduleSlot]


class DoctorDashboard(BaseModel):
    total_patients_today: int
    completed_consultations: int
    pending_patients: int
    average_consultation_time: float
    current_queue: List[dict]
