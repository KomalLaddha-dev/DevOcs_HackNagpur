"""
Patient Service
"""

from sqlalchemy.orm import Session
from typing import List

from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.health_record import HealthRecord
from app.schemas.patient import PatientUpdate, SymptomSubmission, TriageResult
from app.services.triage_service import TriageService


class PatientService:
    """Service for patient operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.triage_service = TriageService()
    
    async def update(self, patient_id: int, data: PatientUpdate) -> Patient:
        """Update patient profile."""
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        
        if patient:
            for key, value in data.dict(exclude_unset=True).items():
                setattr(patient, key, value)
            
            self.db.commit()
            self.db.refresh(patient)
        
        return patient
    
    async def submit_symptoms(self, patient_id: int, symptoms: SymptomSubmission) -> TriageResult:
        """Submit symptoms for AI triage assessment."""
        # Get triage assessment
        result = await self.triage_service.analyze_symptoms(symptoms)
        
        return result
    
    async def get_queue_status(self, patient_id: int) -> dict:
        """Get patient's current queue status."""
        from app.services.queue_service import QueueService
        queue_service = QueueService(self.db)
        return await queue_service.get_position(patient_id)
    
    async def get_appointments(self, patient_id: int) -> List[dict]:
        """Get patient's appointments."""
        appointments = self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.scheduled_time.desc()).all()
        
        return appointments
    
    async def get_health_records(self, patient_id: int) -> List[dict]:
        """Get patient's health records."""
        records = self.db.query(HealthRecord).filter(
            HealthRecord.patient_id == patient_id
        ).order_by(HealthRecord.record_date.desc()).all()
        
        return records
