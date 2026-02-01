"""
Admin Schemas
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class AnalyticsResponse(BaseModel):
    total_patients_today: int
    total_appointments: int
    average_wait_time: float
    triage_distribution: Dict[int, int]
    doctor_utilization: List[Dict]
    hourly_patient_flow: List[Dict]
    queue_length_history: List[Dict]


class SystemSettings(BaseModel):
    max_queue_size: int = 500
    queue_update_interval: int = 300
    emergency_priority_boost: float = 2.0
    teleconsultation_threshold: int = 2
    working_hours_start: str = "08:00"
    working_hours_end: str = "20:00"


class AuditLog(BaseModel):
    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class ReportRequest(BaseModel):
    report_type: str  # daily, weekly, monthly, custom
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_sections: List[str] = ["summary", "details"]
