"""
SmartCare Spare Doctor Pool System
===================================
Cross-hospital doctor allocation for handling patient surges.
Simple load-balancing - NO complex scheduling algorithms.

Features:
1. Maintain pool of available doctors from partner hospitals
2. Threshold-based activation (when local capacity exceeded)
3. Assignment rules (spare doctors handle low-priority cases)
4. Audit logging for all assignments
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from app.core.constants import SPARE_DOCTOR_CONFIG, QUEUE_THRESHOLDS


class DoctorStatus(str, Enum):
    """Doctor availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    ON_BREAK = "on_break"
    ASSIGNED = "assigned"       # Assigned to department
    TELECONSULT = "teleconsult"  # Handling teleconsults
    OFFLINE = "offline"


class DoctorType(str, Enum):
    """Type of doctor in the system."""
    REGULAR = "regular"    # Full-time hospital staff
    SPARE = "spare"        # From spare pool (partner hospitals)
    VISITING = "visiting"  # Visiting consultant


@dataclass
class SpareDoctor:
    """Spare doctor record."""
    doctor_id: int
    name: str
    specialty: str
    hospital_origin: str
    status: DoctorStatus = DoctorStatus.AVAILABLE
    assigned_department: Optional[str] = None
    assigned_at: Optional[datetime] = None
    patients_seen: int = 0
    max_patients: int = 10  # Max patients per assignment
    supports_teleconsult: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "doctor_id": self.doctor_id,
            "name": self.name,
            "specialty": self.specialty,
            "hospital_origin": self.hospital_origin,
            "status": self.status.value,
            "assigned_department": self.assigned_department,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "patients_seen": self.patients_seen,
            "max_patients": self.max_patients,
            "supports_teleconsult": self.supports_teleconsult,
            "available_slots": self.max_patients - self.patients_seen
        }


@dataclass
class AssignmentLog:
    """Audit log for doctor assignments."""
    log_id: str
    doctor_id: int
    doctor_name: str
    action: str  # "assigned", "released", "transferred"
    department: str
    reason: str
    timestamp: datetime
    initiated_by: str  # "system" or admin user ID
    
    def to_dict(self) -> Dict:
        return {
            "log_id": self.log_id,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "action": self.action,
            "department": self.department,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "initiated_by": self.initiated_by
        }


class SpareDoctorPool:
    """
    Manages pool of spare doctors from partner hospitals.
    
    Allocation Rules:
    =================
    1. Spare doctors only activated when utilization > 80%
    2. Spare doctors handle priority 1-2 patients (low risk)
    3. Maximum 3 spare doctors per department
    4. Auto-release when utilization drops below 50%
    
    Assignment Priority:
    - First: Teleconsultation queue
    - Second: Low-priority in-person queue
    - Never: Critical/urgent patients (regular staff only)
    """
    
    def __init__(self):
        self._pool: Dict[int, SpareDoctor] = {}
        self._assignment_logs: List[AssignmentLog] = []
        self._log_counter = 0
        
        # Initialize demo spare doctors
        self._init_demo_pool()
    
    def _init_demo_pool(self):
        """Initialize demo spare doctors for hackathon."""
        demo_doctors = [
            {"id": 1001, "name": "Dr. Sarah Wilson", "specialty": "GENERAL", "hospital": "City Hospital"},
            {"id": 1002, "name": "Dr. James Chen", "specialty": "GENERAL", "hospital": "Metro Clinic"},
            {"id": 1003, "name": "Dr. Priya Sharma", "specialty": "PEDIATRICS", "hospital": "Children's Hospital"},
            {"id": 1004, "name": "Dr. Michael Brown", "specialty": "CARDIOLOGY", "hospital": "Heart Care Center"},
            {"id": 1005, "name": "Dr. Emily Davis", "specialty": "EMERGENCY", "hospital": "Regional Medical"},
            {"id": 1006, "name": "Dr. Raj Patel", "specialty": "ORTHOPEDICS", "hospital": "Bone & Joint Clinic"},
            {"id": 1007, "name": "Dr. Lisa Thompson", "specialty": "DERMATOLOGY", "hospital": "Skin Care Institute"},
            {"id": 1008, "name": "Dr. Ahmed Hassan", "specialty": "NEUROLOGY", "hospital": "Brain Health Center"},
        ]
        
        for doc in demo_doctors:
            self._pool[doc["id"]] = SpareDoctor(
                doctor_id=doc["id"],
                name=doc["name"],
                specialty=doc["specialty"],
                hospital_origin=doc["hospital"]
            )
    
    def get_available_doctors(self, specialty: str = None) -> List[SpareDoctor]:
        """Get list of available spare doctors, optionally filtered by specialty."""
        available = [
            doc for doc in self._pool.values()
            if doc.status == DoctorStatus.AVAILABLE
        ]
        
        if specialty:
            # Filter by specialty (case-insensitive)
            available = [
                doc for doc in available
                if doc.specialty.upper() == specialty.upper()
            ]
        
        return available
    
    def get_assigned_doctors(self, department: str = None) -> List[SpareDoctor]:
        """Get list of currently assigned spare doctors."""
        assigned = [
            doc for doc in self._pool.values()
            if doc.status == DoctorStatus.ASSIGNED
        ]
        
        if department:
            assigned = [
                doc for doc in assigned
                if doc.assigned_department and doc.assigned_department.upper() == department.upper()
            ]
        
        return assigned
    
    def should_activate_spare_doctors(
        self,
        department: str,
        current_queue: int,
        capacity: int,
        current_spare_count: int
    ) -> Dict:
        """
        Determine if spare doctors should be activated.
        
        Returns decision with reasoning.
        """
        if capacity == 0:
            utilization = 100
        else:
            utilization = (current_queue / capacity) * 100
        
        threshold = SPARE_DOCTOR_CONFIG["activation_threshold"] * 100
        max_spare = SPARE_DOCTOR_CONFIG["max_spare_doctors_per_dept"]
        
        should_activate = (
            utilization >= threshold and 
            current_spare_count < max_spare
        )
        
        available = self.get_available_doctors(department)
        
        return {
            "should_activate": should_activate,
            "current_utilization": round(utilization, 1),
            "threshold": threshold,
            "current_spare_doctors": current_spare_count,
            "max_spare_doctors": max_spare,
            "available_in_pool": len(available),
            "reason": self._get_activation_reason(utilization, threshold, current_spare_count, max_spare)
        }
    
    def _get_activation_reason(
        self,
        utilization: float,
        threshold: float,
        current: int,
        max_spare: int
    ) -> str:
        """Generate human-readable activation reason."""
        if utilization < threshold:
            return f"Utilization ({utilization:.0f}%) below threshold ({threshold:.0f}%)"
        elif current >= max_spare:
            return f"Maximum spare doctors ({max_spare}) already assigned"
        else:
            return f"High utilization ({utilization:.0f}%) - spare doctor recommended"
    
    def assign_doctor(
        self,
        doctor_id: int,
        department: str,
        reason: str,
        initiated_by: str = "system"
    ) -> Optional[Dict]:
        """
        Assign a spare doctor to a department.
        
        Returns assignment details or None if failed.
        """
        if doctor_id not in self._pool:
            return None
        
        doctor = self._pool[doctor_id]
        
        if doctor.status != DoctorStatus.AVAILABLE:
            return {
                "success": False,
                "error": f"Doctor is currently {doctor.status.value}"
            }
        
        # Check max spare doctors per department
        current_assigned = len(self.get_assigned_doctors(department))
        if current_assigned >= SPARE_DOCTOR_CONFIG["max_spare_doctors_per_dept"]:
            return {
                "success": False,
                "error": f"Maximum spare doctors ({SPARE_DOCTOR_CONFIG['max_spare_doctors_per_dept']}) already assigned to {department}"
            }
        
        # Assign doctor
        doctor.status = DoctorStatus.ASSIGNED
        doctor.assigned_department = department
        doctor.assigned_at = datetime.utcnow()
        doctor.patients_seen = 0
        
        # Log assignment
        self._log_assignment(doctor, "assigned", department, reason, initiated_by)
        
        return {
            "success": True,
            "doctor": doctor.to_dict(),
            "message": f"Dr. {doctor.name} assigned to {department}"
        }
    
    def release_doctor(
        self,
        doctor_id: int,
        reason: str,
        initiated_by: str = "system"
    ) -> Optional[Dict]:
        """
        Release a spare doctor back to available pool.
        """
        if doctor_id not in self._pool:
            return None
        
        doctor = self._pool[doctor_id]
        old_department = doctor.assigned_department
        
        # Log before changing status
        self._log_assignment(doctor, "released", old_department or "N/A", reason, initiated_by)
        
        # Reset doctor
        doctor.status = DoctorStatus.AVAILABLE
        doctor.assigned_department = None
        doctor.assigned_at = None
        doctor.patients_seen = 0
        
        return {
            "success": True,
            "doctor": doctor.to_dict(),
            "message": f"Dr. {doctor.name} released back to pool"
        }
    
    def auto_assign_to_department(
        self,
        department: str,
        utilization: float,
        initiated_by: str = "system"
    ) -> Optional[Dict]:
        """
        Automatically assign an available spare doctor to overloaded department.
        Uses greedy algorithm - picks first available matching specialist.
        """
        # Get available doctors with matching specialty
        available = self.get_available_doctors(department)
        
        # If no specialists, get general doctors
        if not available:
            available = self.get_available_doctors("GENERAL")
        
        if not available:
            return {
                "success": False,
                "error": "No spare doctors available"
            }
        
        # Pick first available (greedy)
        doctor = available[0]
        
        reason = f"Auto-assigned due to high utilization ({utilization:.0f}%)"
        return self.assign_doctor(doctor.doctor_id, department, reason, initiated_by)
    
    def auto_release_if_underutilized(
        self,
        department: str,
        utilization: float,
        release_threshold: float = 50.0
    ) -> List[Dict]:
        """
        Automatically release spare doctors if department utilization drops.
        """
        if utilization >= release_threshold:
            return []
        
        released = []
        assigned = self.get_assigned_doctors(department)
        
        for doctor in assigned:
            result = self.release_doctor(
                doctor.doctor_id,
                f"Auto-released: utilization dropped to {utilization:.0f}%",
                "system"
            )
            if result and result.get("success"):
                released.append(result)
        
        return released
    
    def record_patient_seen(self, doctor_id: int) -> bool:
        """Record that a spare doctor has seen a patient."""
        if doctor_id not in self._pool:
            return False
        
        doctor = self._pool[doctor_id]
        doctor.patients_seen += 1
        
        # Auto-release if max patients reached
        if doctor.patients_seen >= doctor.max_patients:
            self.release_doctor(
                doctor_id,
                f"Maximum patients ({doctor.max_patients}) reached",
                "system"
            )
        
        return True
    
    def _log_assignment(
        self,
        doctor: SpareDoctor,
        action: str,
        department: str,
        reason: str,
        initiated_by: str
    ):
        """Create audit log entry."""
        self._log_counter += 1
        
        log = AssignmentLog(
            log_id=f"LOG-{self._log_counter:05d}",
            doctor_id=doctor.doctor_id,
            doctor_name=doctor.name,
            action=action,
            department=department,
            reason=reason,
            timestamp=datetime.utcnow(),
            initiated_by=initiated_by
        )
        
        self._assignment_logs.append(log)
    
    def get_assignment_logs(
        self,
        limit: int = 50,
        department: str = None
    ) -> List[Dict]:
        """Get assignment audit logs."""
        logs = self._assignment_logs
        
        if department:
            logs = [l for l in logs if l.department.upper() == department.upper()]
        
        # Return most recent first
        return [l.to_dict() for l in reversed(logs[-limit:])]
    
    def get_pool_status(self) -> Dict:
        """Get overall status of the spare doctor pool."""
        all_doctors = list(self._pool.values())
        
        return {
            "total_doctors": len(all_doctors),
            "available": len([d for d in all_doctors if d.status == DoctorStatus.AVAILABLE]),
            "assigned": len([d for d in all_doctors if d.status == DoctorStatus.ASSIGNED]),
            "on_teleconsult": len([d for d in all_doctors if d.status == DoctorStatus.TELECONSULT]),
            "offline": len([d for d in all_doctors if d.status == DoctorStatus.OFFLINE]),
            "doctors": [d.to_dict() for d in all_doctors]
        }
    
    def get_specialties_available(self) -> Dict[str, int]:
        """Get count of available doctors by specialty."""
        available = self.get_available_doctors()
        
        counts = {}
        for doc in available:
            spec = doc.specialty
            counts[spec] = counts.get(spec, 0) + 1
        
        return counts


# Singleton instance
_spare_pool = None

def get_spare_doctor_pool() -> SpareDoctorPool:
    """Get the global spare doctor pool instance."""
    global _spare_pool
    if _spare_pool is None:
        _spare_pool = SpareDoctorPool()
    return _spare_pool
