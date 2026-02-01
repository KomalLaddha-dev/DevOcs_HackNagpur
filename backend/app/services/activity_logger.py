"""
SmartCare Activity Logger
==========================
Centralized activity logging for audit and monitoring.

Logs:
1. Patient check-ins (with triage scores 1-10)
2. Spare doctor assignments/releases
3. Emergency overrides
4. AI allocation decisions
5. System events
"""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class ActivityType(str, Enum):
    """Types of activities logged."""
    PATIENT_CHECKIN = "patient_checkin"
    PATIENT_CALLED = "patient_called"
    PATIENT_COMPLETED = "patient_completed"
    DOCTOR_ASSIGNED = "doctor_assigned"
    DOCTOR_RELEASED = "doctor_released"
    EMERGENCY_OVERRIDE = "emergency_override"
    AI_ALLOCATION = "ai_allocation"
    SYSTEM_EVENT = "system_event"


@dataclass
class ActivityLog:
    """Activity log entry."""
    log_id: str
    activity_type: ActivityType
    timestamp: datetime
    title: str
    description: str
    details: Dict
    severity_score: Optional[int] = None  # 1-10 scale
    department: Optional[str] = None
    actor: str = "system"  # Who performed the action
    
    def to_dict(self) -> Dict:
        return {
            "log_id": self.log_id,
            "activity_type": self.activity_type.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "details": self.details,
            "severity_score": self.severity_score,
            "severity_label": self._get_severity_label(),
            "department": self.department,
            "actor": self.actor
        }
    
    def _get_severity_label(self) -> str:
        """Convert 1-10 score to label."""
        if self.severity_score is None:
            return "N/A"
        if self.severity_score >= 9:
            return "CRITICAL"
        elif self.severity_score >= 7:
            return "HIGH"
        elif self.severity_score >= 5:
            return "MODERATE"
        elif self.severity_score >= 3:
            return "LOW"
        else:
            return "ROUTINE"


class ActivityLogger:
    """
    Centralized activity logging system.
    
    Maintains in-memory log for demo (would use database in production).
    """
    
    def __init__(self):
        self._logs: List[ActivityLog] = []
        self._log_counter = 0
    
    def _generate_id(self) -> str:
        """Generate unique log ID."""
        self._log_counter += 1
        return f"ACT-{self._log_counter:06d}"
    
    def log_patient_checkin(
        self,
        patient_name: str,
        patient_id: int,
        entry_id: int,
        token: str,
        department: str,
        symptoms: List[str],
        triage_score: int,
        severity_level: str,
        priority_score: float,
        wait_minutes: int
    ):
        """Log patient check-in event."""
        # Triage score is now already on 1-10 scale
        severity_10 = triage_score
        
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.PATIENT_CHECKIN,
            timestamp=datetime.utcnow(),
            title=f"Patient Check-In: {patient_name}",
            description=f"{patient_name} checked in to {department.capitalize()} department",
            details={
                "patient_id": patient_id,
                "patient_name": patient_name,
                "entry_id": entry_id,
                "token": token,
                "symptoms": symptoms,
                "triage_score_5": triage_score,
                "triage_score_10": severity_10,
                "severity_level": severity_level,
                "priority_score": priority_score,
                "estimated_wait": wait_minutes
            },
            severity_score=severity_10,
            department=department,
            actor="patient_self"
        )
        self._logs.append(log)
        return log.to_dict()
    
    def log_patient_called(
        self,
        patient_name: str,
        entry_id: str,
        department: str,
        doctor_name: str = "Doctor"
    ):
        """Log patient being called to see doctor."""
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.PATIENT_CALLED,
            timestamp=datetime.utcnow(),
            title=f"Patient Called: {patient_name}",
            description=f"{patient_name} called to see doctor in {department.capitalize()}",
            details={
                "entry_id": entry_id,
                "patient_name": patient_name,
                "called_by": doctor_name
            },
            department=department,
            actor=doctor_name
        )
        self._logs.append(log)
        return log.to_dict()
    
    def log_patient_completed(
        self,
        patient_name: str,
        entry_id: str,
        department: str,
        doctor_name: str = "Doctor"
    ):
        """Log patient consultation completed."""
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.PATIENT_COMPLETED,
            timestamp=datetime.utcnow(),
            title=f"Consultation Complete: {patient_name}",
            description=f"{patient_name}'s consultation completed in {department.capitalize()}",
            details={
                "entry_id": entry_id,
                "patient_name": patient_name,
                "completed_by": doctor_name
            },
            department=department,
            actor=doctor_name
        )
        self._logs.append(log)
        return log.to_dict()
    
    def log_doctor_assigned(
        self,
        doctor_id: int,
        doctor_name: str,
        department: str,
        reason: str,
        initiated_by: str = "system"
    ):
        """Log spare doctor assignment."""
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.DOCTOR_ASSIGNED,
            timestamp=datetime.utcnow(),
            title=f"Doctor Assigned: {doctor_name}",
            description=f"{doctor_name} assigned to {department.capitalize()} department",
            details={
                "doctor_id": doctor_id,
                "doctor_name": doctor_name,
                "department": department,
                "reason": reason,
                "initiated_by": initiated_by
            },
            department=department,
            actor=initiated_by
        )
        self._logs.append(log)
        return log.to_dict()
    
    def log_doctor_released(
        self,
        doctor_id: int,
        doctor_name: str,
        department: str,
        reason: str,
        initiated_by: str = "system"
    ):
        """Log spare doctor release."""
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.DOCTOR_RELEASED,
            timestamp=datetime.utcnow(),
            title=f"Doctor Released: {doctor_name}",
            description=f"{doctor_name} released from {department.capitalize()} department",
            details={
                "doctor_id": doctor_id,
                "doctor_name": doctor_name,
                "department": department,
                "reason": reason,
                "initiated_by": initiated_by
            },
            department=department,
            actor=initiated_by
        )
        self._logs.append(log)
        return log.to_dict()
    
    def log_emergency_override(
        self,
        patient_name: str,
        entry_id: str,
        old_severity: str,
        new_severity: str,
        reason: str,
        authorized_by: str
    ):
        """Log emergency priority override."""
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.EMERGENCY_OVERRIDE,
            timestamp=datetime.utcnow(),
            title=f"Emergency Override: {patient_name}",
            description=f"{patient_name} escalated from {old_severity} to {new_severity}",
            details={
                "entry_id": entry_id,
                "patient_name": patient_name,
                "old_severity": old_severity,
                "new_severity": new_severity,
                "reason": reason,
                "authorized_by": authorized_by
            },
            severity_score=10,  # Emergency overrides are always high severity
            actor=authorized_by
        )
        self._logs.append(log)
        return log.to_dict()
    
    def log_ai_allocation(
        self,
        action: str,
        department: str,
        doctor_name: Optional[str],
        reason: str,
        confidence: float,
        executed: bool
    ):
        """Log AI allocation decision."""
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.AI_ALLOCATION,
            timestamp=datetime.utcnow(),
            title=f"AI Decision: {action.capitalize()} for {department.capitalize()}",
            description=f"AI {'executed' if executed else 'recommended'} {action} for {department}",
            details={
                "action": action,
                "department": department,
                "doctor_name": doctor_name,
                "reason": reason,
                "confidence": round(confidence * 100),
                "executed": executed
            },
            department=department,
            actor="ai_system"
        )
        self._logs.append(log)
        return log.to_dict()
    
    def log_system_event(
        self,
        title: str,
        description: str,
        details: Dict = None
    ):
        """Log general system event."""
        log = ActivityLog(
            log_id=self._generate_id(),
            activity_type=ActivityType.SYSTEM_EVENT,
            timestamp=datetime.utcnow(),
            title=title,
            description=description,
            details=details or {},
            actor="system"
        )
        self._logs.append(log)
        return log.to_dict()
    
    def get_logs(
        self,
        limit: int = 100,
        activity_type: Optional[str] = None,
        department: Optional[str] = None
    ) -> List[Dict]:
        """Get activity logs with optional filtering."""
        logs = self._logs
        
        if activity_type:
            logs = [l for l in logs if l.activity_type.value == activity_type]
        
        if department:
            logs = [l for l in logs if l.department and l.department.lower() == department.lower()]
        
        # Return most recent first
        return [l.to_dict() for l in reversed(logs[-limit:])]
    
    def get_stats(self) -> Dict:
        """Get activity statistics."""
        now = datetime.utcnow()
        
        # Count by type
        type_counts = {}
        for log in self._logs:
            t = log.activity_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Count check-ins by severity
        severity_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0, "routine": 0}
        for log in self._logs:
            if log.activity_type == ActivityType.PATIENT_CHECKIN and log.severity_score:
                if log.severity_score >= 9:
                    severity_counts["critical"] += 1
                elif log.severity_score >= 7:
                    severity_counts["high"] += 1
                elif log.severity_score >= 5:
                    severity_counts["moderate"] += 1
                elif log.severity_score >= 3:
                    severity_counts["low"] += 1
                else:
                    severity_counts["routine"] += 1
        
        return {
            "total_logs": len(self._logs),
            "by_type": type_counts,
            "checkin_severity": severity_counts,
            "total_checkins": type_counts.get("patient_checkin", 0),
            "total_doctor_assignments": type_counts.get("doctor_assigned", 0),
            "total_ai_decisions": type_counts.get("ai_allocation", 0),
            "total_overrides": type_counts.get("emergency_override", 0)
        }


# Singleton instance
_activity_logger = None

def get_activity_logger() -> ActivityLogger:
    """Get the global activity logger instance."""
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = ActivityLogger()
    return _activity_logger
