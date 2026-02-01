"""
Doctor Service
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.doctor import Doctor, DoctorSchedule
from app.schemas.doctor import AvailabilityUpdate, DoctorDashboard


class DoctorService:
    """Service for doctor operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def list_doctors(
        self,
        specialty: Optional[str] = None,
        available: Optional[bool] = None
    ) -> List[Doctor]:
        """List doctors with optional filters."""
        query = self.db.query(Doctor)
        
        if specialty:
            query = query.filter(Doctor.specialty == specialty)
        if available is not None:
            query = query.filter(Doctor.is_available == available)
        
        return query.all()
    
    async def get_doctor(self, doctor_id: int) -> Optional[Doctor]:
        """Get specific doctor."""
        return self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
    
    async def get_schedule(self, doctor_id: int) -> dict:
        """Get doctor's schedule."""
        schedules = self.db.query(DoctorSchedule).filter(
            DoctorSchedule.doctor_id == doctor_id
        ).all()
        
        return {
            "doctor_id": doctor_id,
            "slots": schedules
        }
    
    async def update_availability(
        self,
        doctor_id: int,
        availability: AvailabilityUpdate
    ) -> Doctor:
        """Update doctor's availability."""
        doctor = await self.get_doctor(doctor_id)
        
        if doctor:
            doctor.is_available = availability.is_available
            self.db.commit()
            self.db.refresh(doctor)
        
        return doctor
    
    async def get_dashboard(self, doctor_id: int) -> DoctorDashboard:
        """Get doctor's dashboard data."""
        from app.models.appointment import Appointment
        from app.models.queue import QueueEntry
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        
        # Get today's stats
        total_today = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_time >= today
        ).count()
        
        completed = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "completed",
            Appointment.scheduled_time >= today
        ).count()
        
        pending = self.db.query(QueueEntry).filter(
            QueueEntry.doctor_id == doctor_id,
            QueueEntry.status == "waiting"
        ).count()
        
        return DoctorDashboard(
            total_patients_today=total_today,
            completed_consultations=completed,
            pending_patients=pending,
            average_consultation_time=12.5,
            current_queue=[]
        )
    
    async def get_assigned_patients(self, doctor_id: int) -> List[dict]:
        """Get patients currently assigned to doctor."""
        from app.models.queue import QueueEntry
        
        entries = self.db.query(QueueEntry).filter(
            QueueEntry.doctor_id == doctor_id,
            QueueEntry.status.in_(["waiting", "called"])
        ).order_by(QueueEntry.priority_score.desc()).all()
        
        return entries
