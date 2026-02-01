"""
Queue Schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CheckInRequest(BaseModel):
    patient_id: int
    symptoms: Optional[str] = None
    appointment_id: Optional[int] = None


class QueueEntry(BaseModel):
    id: int
    patient_id: int
    token_number: str
    triage_score: int
    priority_score: float
    status: str
    check_in_time: datetime
    estimated_wait_time: Optional[int] = None
    position: Optional[int] = None

    class Config:
        from_attributes = True


class QueueStatus(BaseModel):
    patient_id: int
    token_number: str
    position: int
    estimated_wait_time: int
    status: str
    triage_score: int
    priority_score: float
    people_ahead: int


class QueueUpdate(BaseModel):
    queue_id: int
    action: str  # call, complete, cancel
    notes: Optional[str] = None
