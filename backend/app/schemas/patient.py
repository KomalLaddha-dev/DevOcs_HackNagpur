"""
Patient Schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class PatientCreate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None


class PatientUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    user_id: int
    date_of_birth: Optional[date]
    gender: Optional[str]
    blood_group: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SymptomSubmission(BaseModel):
    symptoms: List[str]
    description: str
    duration: str
    severity_self_assessment: int  # 1-10
    additional_notes: Optional[str] = None


class TriageResult(BaseModel):
    triage_score: int  # 1-5
    severity_level: str
    recommended_action: str
    estimated_wait_time: int  # minutes
    priority_score: float
    explanation: str
