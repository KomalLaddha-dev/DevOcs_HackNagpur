"""
SmartCare Emergency Override System
====================================
Manual override for emergency situations with full audit logging.
Critical for real-world hospital deployments.

Features:
1. Instant priority boost for emergency patients
2. Complete audit trail (who, when, why)
3. Admin/Doctor authorization required
4. Automatic queue reordering
"""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from app.services.priority_queue import get_priority_queue


class OverrideType(str, Enum):
    """Types of emergency overrides."""
    EMERGENCY_ESCALATE = "emergency_escalate"  # Move to top of queue
    PRIORITY_BOOST = "priority_boost"          # Increase priority
    IMMEDIATE_ATTENTION = "immediate_attention"  # Flag for immediate care
    TRANSFER_CRITICAL = "transfer_critical"    # Transfer to critical care
    SKIP_TRIAGE = "skip_triage"                # Skip triage for known critical


class OverrideReason(str, Enum):
    """Standard reasons for override (for audit)."""
    CLINICAL_DETERIORATION = "Clinical deterioration"
    NEW_CRITICAL_SYMPTOM = "New critical symptom observed"
    VITAL_SIGNS_ABNORMAL = "Abnormal vital signs"
    DOCTOR_JUDGMENT = "Doctor clinical judgment"
    FAMILY_EMERGENCY = "Family emergency situation"
    AMBULANCE_ARRIVAL = "Ambulance arrival - pre-triaged"
    REFERRED_CRITICAL = "Referred as critical from other facility"
    OTHER = "Other (see notes)"


@dataclass
class OverrideLog:
    """Complete audit log entry for override."""
    log_id: str
    timestamp: datetime
    override_type: OverrideType
    patient_id: int
    patient_name: str
    queue_entry_id: int
    
    # What changed
    previous_priority: float
    new_priority: float
    previous_position: int
    new_position: int
    
    # Authorization
    authorized_by_id: int
    authorized_by_name: str
    authorized_by_role: str  # "doctor", "admin", "nurse"
    
    # Justification
    reason_code: OverrideReason
    reason_notes: str
    
    # Result
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "override_type": self.override_type.value,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "queue_entry_id": self.queue_entry_id,
            "previous_priority": self.previous_priority,
            "new_priority": self.new_priority,
            "previous_position": self.previous_position,
            "new_position": self.new_position,
            "authorized_by": {
                "id": self.authorized_by_id,
                "name": self.authorized_by_name,
                "role": self.authorized_by_role
            },
            "reason": {
                "code": self.reason_code.value,
                "notes": self.reason_notes
            },
            "success": self.success,
            "error_message": self.error_message
        }


class EmergencyOverrideSystem:
    """
    Emergency override system with audit logging.
    
    Authorization Rules:
    ====================
    - EMERGENCY_ESCALATE: Doctor, Admin
    - PRIORITY_BOOST: Doctor, Admin, Senior Nurse
    - IMMEDIATE_ATTENTION: Doctor only
    - TRANSFER_CRITICAL: Doctor, Admin
    - SKIP_TRIAGE: Doctor (for ambulance arrivals)
    
    All overrides are logged and can be audited.
    """
    
    AUTHORIZATION_MATRIX = {
        OverrideType.EMERGENCY_ESCALATE: ["doctor", "admin"],
        OverrideType.PRIORITY_BOOST: ["doctor", "admin", "nurse"],
        OverrideType.IMMEDIATE_ATTENTION: ["doctor"],
        OverrideType.TRANSFER_CRITICAL: ["doctor", "admin"],
        OverrideType.SKIP_TRIAGE: ["doctor"],
    }
    
    def __init__(self):
        self._logs: List[OverrideLog] = []
        self._log_counter = 0
    
    def _generate_log_id(self) -> str:
        """Generate unique log ID."""
        self._log_counter += 1
        return f"OVR-{datetime.utcnow().strftime('%Y%m%d')}-{self._log_counter:05d}"
    
    def check_authorization(
        self,
        override_type: OverrideType,
        user_role: str
    ) -> Dict:
        """Check if user is authorized for this override type."""
        allowed_roles = self.AUTHORIZATION_MATRIX.get(override_type, [])
        is_authorized = user_role.lower() in allowed_roles
        
        return {
            "authorized": is_authorized,
            "override_type": override_type.value,
            "user_role": user_role,
            "allowed_roles": allowed_roles,
            "message": "Authorized" if is_authorized else f"Only {', '.join(allowed_roles)} can perform this override"
        }
    
    def emergency_escalate(
        self,
        queue_entry_id: int,
        patient_id: int,
        patient_name: str,
        authorized_by_id: int,
        authorized_by_name: str,
        authorized_by_role: str,
        reason_code: OverrideReason,
        reason_notes: str = ""
    ) -> Dict:
        """
        Emergency escalate - move patient to top of queue.
        
        This is the most critical override, used for:
        - Sudden clinical deterioration
        - Critical vital signs
        - Doctor's emergency judgment
        """
        # Check authorization
        auth = self.check_authorization(OverrideType.EMERGENCY_ESCALATE, authorized_by_role)
        if not auth["authorized"]:
            return {
                "success": False,
                "error": auth["message"]
            }
        
        # Get priority queue
        pq = get_priority_queue()
        
        # Get current state (for logging)
        queue_list = pq.get_queue_list()
        current_entry = None
        previous_position = 0
        previous_priority = 0
        
        for i, entry in enumerate(queue_list):
            if entry["entry_id"] == queue_entry_id:
                current_entry = entry
                previous_position = entry["position"]
                previous_priority = entry["priority_score"]
                break
        
        if not current_entry:
            return {
                "success": False,
                "error": f"Queue entry {queue_entry_id} not found"
            }
        
        # Perform emergency override
        new_priority = pq.emergency_override(queue_entry_id)
        
        if new_priority is None:
            return {
                "success": False,
                "error": "Failed to apply emergency override"
            }
        
        # Get new position
        new_queue = pq.get_queue_list()
        new_position = 1  # Emergency should be at top
        for entry in new_queue:
            if entry["entry_id"] == queue_entry_id:
                new_position = entry["position"]
                break
        
        # Create audit log
        log = OverrideLog(
            log_id=self._generate_log_id(),
            timestamp=datetime.utcnow(),
            override_type=OverrideType.EMERGENCY_ESCALATE,
            patient_id=patient_id,
            patient_name=patient_name,
            queue_entry_id=queue_entry_id,
            previous_priority=previous_priority,
            new_priority=new_priority,
            previous_position=previous_position,
            new_position=new_position,
            authorized_by_id=authorized_by_id,
            authorized_by_name=authorized_by_name,
            authorized_by_role=authorized_by_role,
            reason_code=reason_code,
            reason_notes=reason_notes,
            success=True
        )
        
        self._logs.append(log)
        
        return {
            "success": True,
            "log_id": log.log_id,
            "message": f"Patient {patient_name} moved to position {new_position}",
            "previous_position": previous_position,
            "new_position": new_position,
            "new_priority": new_priority,
            "audit_log": log.to_dict()
        }
    
    def priority_boost(
        self,
        queue_entry_id: int,
        patient_id: int,
        patient_name: str,
        boost_amount: int,  # 1-3 severity levels
        authorized_by_id: int,
        authorized_by_name: str,
        authorized_by_role: str,
        reason_code: OverrideReason,
        reason_notes: str = ""
    ) -> Dict:
        """
        Boost patient priority by specified amount.
        
        Less aggressive than emergency_escalate.
        For situations where patient needs to be seen sooner but not immediately.
        """
        # Check authorization
        auth = self.check_authorization(OverrideType.PRIORITY_BOOST, authorized_by_role)
        if not auth["authorized"]:
            return {
                "success": False,
                "error": auth["message"]
            }
        
        # Validate boost amount
        boost_amount = max(1, min(3, boost_amount))
        
        pq = get_priority_queue()
        
        # Get current state
        queue_list = pq.get_queue_list()
        current_entry = None
        previous_position = 0
        previous_priority = 0
        current_triage = 3
        
        for entry in queue_list:
            if entry["entry_id"] == queue_entry_id:
                current_entry = entry
                previous_position = entry["position"]
                previous_priority = entry["priority_score"]
                current_triage = entry["triage_score"]
                break
        
        if not current_entry:
            return {
                "success": False,
                "error": f"Queue entry {queue_entry_id} not found"
            }
        
        # Calculate new triage score (don't exceed 5)
        new_triage = min(5, current_triage + boost_amount)
        
        # Update priority
        new_priority = pq.update_priority(
            entry_id=queue_entry_id,
            new_triage_score=new_triage
        )
        
        if new_priority is None:
            return {
                "success": False,
                "error": "Failed to update priority"
            }
        
        # Get new position
        new_queue = pq.get_queue_list()
        new_position = previous_position
        for entry in new_queue:
            if entry["entry_id"] == queue_entry_id:
                new_position = entry["position"]
                break
        
        # Create audit log
        log = OverrideLog(
            log_id=self._generate_log_id(),
            timestamp=datetime.utcnow(),
            override_type=OverrideType.PRIORITY_BOOST,
            patient_id=patient_id,
            patient_name=patient_name,
            queue_entry_id=queue_entry_id,
            previous_priority=previous_priority,
            new_priority=new_priority,
            previous_position=previous_position,
            new_position=new_position,
            authorized_by_id=authorized_by_id,
            authorized_by_name=authorized_by_name,
            authorized_by_role=authorized_by_role,
            reason_code=reason_code,
            reason_notes=f"Boost amount: +{boost_amount}. {reason_notes}",
            success=True
        )
        
        self._logs.append(log)
        
        return {
            "success": True,
            "log_id": log.log_id,
            "message": f"Patient {patient_name} priority boosted by {boost_amount}",
            "previous_position": previous_position,
            "new_position": new_position,
            "triage_change": f"{current_triage} → {new_triage}",
            "audit_log": log.to_dict()
        }
    
    def get_override_logs(
        self,
        limit: int = 100,
        patient_id: int = None,
        authorized_by_id: int = None,
        override_type: OverrideType = None
    ) -> List[Dict]:
        """Get override audit logs with optional filtering."""
        logs = self._logs
        
        if patient_id:
            logs = [l for l in logs if l.patient_id == patient_id]
        
        if authorized_by_id:
            logs = [l for l in logs if l.authorized_by_id == authorized_by_id]
        
        if override_type:
            logs = [l for l in logs if l.override_type == override_type]
        
        # Return most recent first
        return [l.to_dict() for l in reversed(logs[-limit:])]
    
    def get_override_stats(self) -> Dict:
        """Get statistics about overrides."""
        if not self._logs:
            return {
                "total_overrides": 0,
                "by_type": {},
                "by_role": {},
                "success_rate": 100.0
            }
        
        by_type = {}
        by_role = {}
        successful = 0
        
        for log in self._logs:
            # Count by type
            t = log.override_type.value
            by_type[t] = by_type.get(t, 0) + 1
            
            # Count by role
            r = log.authorized_by_role
            by_role[r] = by_role.get(r, 0) + 1
            
            if log.success:
                successful += 1
        
        return {
            "total_overrides": len(self._logs),
            "by_type": by_type,
            "by_role": by_role,
            "success_rate": round(successful / len(self._logs) * 100, 1),
            "last_override": self._logs[-1].to_dict() if self._logs else None
        }


# Singleton instance
_override_system = None

def get_override_system() -> EmergencyOverrideSystem:
    """Get the global emergency override system."""
    global _override_system
    if _override_system is None:
        _override_system = EmergencyOverrideSystem()
    return _override_system
