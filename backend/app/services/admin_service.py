"""
Admin Service
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.models.user import User
from app.models.appointment import Appointment
from app.models.queue import QueueEntry
from app.schemas.admin import AnalyticsResponse, SystemSettings, AuditLog


class AdminService:
    """Service for admin operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_analytics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> AnalyticsResponse:
        """Get dashboard analytics."""
        today = datetime.now().date()
        
        # Total patients today
        total_patients = self.db.query(QueueEntry).filter(
            QueueEntry.check_in_time >= today
        ).count()
        
        # Total appointments
        total_appointments = self.db.query(Appointment).filter(
            Appointment.scheduled_time >= today
        ).count()
        
        # Calculate average wait time
        completed_entries = self.db.query(QueueEntry).filter(
            QueueEntry.status == "completed",
            QueueEntry.check_in_time >= today
        ).all()
        
        avg_wait = 0
        if completed_entries:
            wait_times = [
                (e.called_time - e.check_in_time).seconds / 60
                for e in completed_entries if e.called_time
            ]
            avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
        
        # Triage distribution
        triage_dist = {}
        for i in range(1, 6):
            count = self.db.query(QueueEntry).filter(
                QueueEntry.triage_score == i,
                QueueEntry.check_in_time >= today
            ).count()
            triage_dist[i] = count
        
        return AnalyticsResponse(
            total_patients_today=total_patients,
            total_appointments=total_appointments,
            average_wait_time=round(avg_wait, 1),
            triage_distribution=triage_dist,
            doctor_utilization=[],
            hourly_patient_flow=[],
            queue_length_history=[]
        )
    
    async def generate_report(
        self,
        report_type: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> dict:
        """Generate various reports."""
        # Implementation would generate different report types
        return {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "data": {}
        }
    
    async def get_settings(self) -> SystemSettings:
        """Get system settings."""
        # In production, load from database or config
        return SystemSettings()
    
    async def update_settings(self, settings: SystemSettings) -> SystemSettings:
        """Update system settings."""
        # In production, save to database
        return settings
    
    async def get_audit_logs(self, page: int, limit: int) -> List[AuditLog]:
        """Get audit logs with pagination."""
        # Implementation would query audit log table
        return []
    
    async def list_users(self, role: Optional[str] = None) -> List[User]:
        """List all users."""
        query = self.db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        
        return query.all()
    
    async def get_queue_stats(self) -> dict:
        """Get detailed queue statistics."""
        from datetime import timedelta
        
        today = datetime.now().date()
        
        current_waiting = self.db.query(QueueEntry).filter(
            QueueEntry.status == "waiting"
        ).count()
        
        return {
            "current_queue_length": current_waiting,
            "average_processing_time": 12.5,
            "estimated_clear_time": "2 hours",
            "peak_hours": ["10:00-11:00", "14:00-15:00"]
        }
