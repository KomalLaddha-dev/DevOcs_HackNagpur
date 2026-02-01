"""
Appointment Service
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class AppointmentService:
    """Service for appointment operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, data: AppointmentCreate, patient_id: int) -> Appointment:
        """Create a new appointment."""
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=data.doctor_id,
            scheduled_time=data.scheduled_time,
            appointment_type=data.appointment_type,
            symptoms=data.symptoms,
            status=AppointmentStatus.SCHEDULED
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    async def get(self, appointment_id: int) -> Optional[Appointment]:
        """Get specific appointment."""
        return self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    async def list_appointments(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None
    ) -> List[Appointment]:
        """List appointments with filters."""
        query = self.db.query(Appointment)
        
        if date_from:
            query = query.filter(Appointment.scheduled_time >= date_from)
        if date_to:
            query = query.filter(Appointment.scheduled_time <= date_to)
        if status:
            query = query.filter(Appointment.status == status)
        
        return query.order_by(Appointment.scheduled_time).all()
    
    async def update(self, appointment_id: int, data: AppointmentUpdate) -> Appointment:
        """Update appointment."""
        appointment = await self.get(appointment_id)
        
        if appointment:
            for key, value in data.dict(exclude_unset=True).items():
                setattr(appointment, key, value)
            
            self.db.commit()
            self.db.refresh(appointment)
        
        return appointment
    
    async def cancel(self, appointment_id: int) -> None:
        """Cancel appointment."""
        appointment = await self.get(appointment_id)
        
        if appointment:
            appointment.status = AppointmentStatus.CANCELLED
            self.db.commit()
    
    async def complete(self, appointment_id: int, notes: Optional[str] = None) -> Appointment:
        """Mark appointment as completed."""
        appointment = await self.get(appointment_id)
        
        if appointment:
            appointment.status = AppointmentStatus.COMPLETED
            appointment.actual_end_time = datetime.utcnow()
            if notes:
                appointment.notes = notes
            self.db.commit()
            self.db.refresh(appointment)
        
        return appointment
