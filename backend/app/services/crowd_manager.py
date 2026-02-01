"""
SmartCare Crowd Management System
==================================
Handles queue overflow, wait time estimation, and auto-redirect.
Simple threshold-based logic - NO heavy AI.

Features:
1. Real-time queue length monitoring per department
2. Automatic redirect to teleconsult for low-risk patients
3. Expected wait time calculation
4. Peak hour detection and load balancing suggestions
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from app.core.constants import (
    QUEUE_THRESHOLDS, BASE_WAIT_TIMES, TELECONSULT_ELIGIBLE,
    DEPARTMENTS, SEVERITY_DESCRIPTIONS
)


class CrowdLevel(str, Enum):
    """Queue congestion levels."""
    LOW = "low"           # < 50% capacity
    MODERATE = "moderate"  # 50-80% capacity  
    HIGH = "high"         # 80-100% capacity
    CRITICAL = "critical"  # > 100% capacity


@dataclass
class DepartmentStatus:
    """Status of a single department."""
    department: str
    code: str
    current_queue: int
    capacity: int
    crowd_level: CrowdLevel
    avg_wait_minutes: int
    active_doctors: int
    spare_doctors_assigned: int
    teleconsult_redirects: int
    
    @property
    def utilization(self) -> float:
        """Calculate utilization percentage."""
        return (self.current_queue / self.capacity * 100) if self.capacity > 0 else 0
    
    def to_dict(self) -> Dict:
        # Map crowd_level to frontend status
        status_map = {
            CrowdLevel.LOW: "normal",
            CrowdLevel.MODERATE: "normal",
            CrowdLevel.HIGH: "busy",
            CrowdLevel.CRITICAL: "overloaded"
        }
        return {
            "department": self.department,
            "code": self.code,
            "current_queue": self.current_queue,
            "current_patients": self.current_queue,  # Alias for frontend
            "capacity": self.capacity,
            "crowd_level": self.crowd_level.value,
            "status": status_map.get(self.crowd_level, "normal"),  # Frontend expected field
            "load_percentage": round(self.utilization, 1),  # Frontend expected field
            "avg_wait_minutes": self.avg_wait_minutes,
            "utilization_percent": round(self.utilization, 1),
            "active_doctors": self.active_doctors,
            "spare_doctors_assigned": self.spare_doctors_assigned,
            "teleconsult_redirects": self.teleconsult_redirects
        }


class CrowdManager:
    """
    Crowd management and load balancing system.
    
    Decision Logic:
    ===============
    1. Queue < 50% capacity → Normal operation
    2. Queue 50-80% → Show warning, no action
    3. Queue 80-100% → Auto-redirect low-risk to teleconsult
    4. Queue > 100% → Request spare doctors + teleconsult redirect
    """
    
    def __init__(self):
        # Track department statuses (in production, this would be from DB)
        self._department_stats: Dict[str, DepartmentStatus] = {}
        self._teleconsult_queue: List[Dict] = []
        self._redirect_history: List[Dict] = []
    
    def calculate_crowd_level(self, current: int, capacity: int) -> CrowdLevel:
        """
        Determine crowd level based on queue-to-capacity ratio.
        
        Thresholds (easily adjustable):
        - LOW: < 50%
        - MODERATE: 50-80%
        - HIGH: 80-100%
        - CRITICAL: > 100%
        """
        if capacity == 0:
            return CrowdLevel.CRITICAL
        
        ratio = current / capacity
        
        if ratio < 0.5:
            return CrowdLevel.LOW
        elif ratio < 0.8:
            return CrowdLevel.MODERATE
        elif ratio <= 1.0:
            return CrowdLevel.HIGH
        else:
            return CrowdLevel.CRITICAL
    
    def calculate_expected_wait(
        self,
        position: int,
        triage_score: int,
        avg_consultation_minutes: int = 15,
        active_doctors: int = 1
    ) -> Dict:
        """
        Calculate expected wait time for a patient.
        
        Formula:
        ========
        base_wait = position × avg_consultation_time / active_doctors
        adjusted_wait = base_wait × severity_factor
        
        Severity Factor:
        - Critical (5): 0.1 (immediate)
        - Urgent (4): 0.3
        - Moderate (3): 0.7
        - Low (2): 1.0
        - Minimal (1): 1.2 (can wait longer)
        """
        severity_factors = {5: 0.1, 4: 0.3, 3: 0.7, 2: 1.0, 1: 1.2}
        factor = severity_factors.get(triage_score, 1.0)
        
        # Base calculation
        if active_doctors > 0:
            base_wait = (position * avg_consultation_minutes) / active_doctors
        else:
            base_wait = position * avg_consultation_minutes
        
        adjusted_wait = base_wait * factor
        
        # Add buffer for uncertainty
        min_wait = max(0, int(adjusted_wait * 0.8))
        max_wait = int(adjusted_wait * 1.3)
        
        return {
            "estimated_minutes": int(adjusted_wait),
            "range_min": min_wait,
            "range_max": max_wait,
            "position": position,
            "explanation": f"Based on {position} patients ahead, {active_doctors} active doctors"
        }
    
    def should_redirect_to_teleconsult(
        self,
        triage_score: int,
        crowd_level: CrowdLevel,
        patient_preference: bool = True
    ) -> Dict:
        """
        Determine if patient should be redirected to teleconsultation.
        
        Rules:
        - Only severity 1-2 patients eligible
        - Auto-suggest when crowd level is HIGH or CRITICAL
        - Respect patient preference (can decline)
        """
        eligible = triage_score <= TELECONSULT_ELIGIBLE["max_severity_score"]
        
        # Auto-redirect conditions
        should_redirect = eligible and crowd_level in [CrowdLevel.HIGH, CrowdLevel.CRITICAL]
        
        # Soft suggest even at moderate
        soft_suggest = eligible and crowd_level == CrowdLevel.MODERATE
        
        return {
            "eligible": eligible,
            "recommended": should_redirect,
            "soft_suggest": soft_suggest or should_redirect,
            "reason": self._get_redirect_reason(triage_score, crowd_level, eligible),
            "benefits": [
                "No waiting in queue",
                "Consult from comfort of home",
                "Prescription sent digitally",
                "Lower consultation fee"
            ] if eligible else []
        }
    
    def _get_redirect_reason(
        self,
        triage_score: int,
        crowd_level: CrowdLevel,
        eligible: bool
    ) -> str:
        """Generate human-readable reason for redirect decision."""
        if not eligible:
            return "Your condition requires in-person examination"
        
        if crowd_level == CrowdLevel.CRITICAL:
            return "Hospital is extremely busy. Teleconsult recommended for faster care."
        elif crowd_level == CrowdLevel.HIGH:
            return "Long wait times expected. Consider teleconsult for convenience."
        elif crowd_level == CrowdLevel.MODERATE:
            return "Teleconsult available as a convenient alternative."
        else:
            return "Teleconsult is an option for your condition."
    
    def get_department_status(self, department: str) -> Optional[DepartmentStatus]:
        """Get current status of a department."""
        return self._department_stats.get(department)
    
    def update_department_status(
        self,
        department: str,
        current_queue: int,
        active_doctors: int,
        spare_doctors: int = 0,
        teleconsult_redirects: int = 0
    ) -> DepartmentStatus:
        """Update and return department status."""
        dept_info = DEPARTMENTS.get(department, {"code": "GEN", "base_capacity": 30})
        
        # Capacity scales with doctors
        effective_capacity = dept_info["base_capacity"] * max(1, active_doctors)
        
        # Calculate crowd level
        crowd_level = self.calculate_crowd_level(current_queue, effective_capacity)
        
        # Estimate avg wait (simplified)
        if active_doctors > 0:
            avg_wait = int((current_queue / active_doctors) * 15)  # 15 min per patient
        else:
            avg_wait = current_queue * 15
        
        status = DepartmentStatus(
            department=department,
            code=dept_info["code"],
            current_queue=current_queue,
            capacity=effective_capacity,
            crowd_level=crowd_level,
            avg_wait_minutes=avg_wait,
            active_doctors=active_doctors,
            spare_doctors_assigned=spare_doctors,
            teleconsult_redirects=teleconsult_redirects
        )
        
        self._department_stats[department] = status
        return status
    
    def get_all_departments_status(self) -> List[Dict]:
        """Get status of all departments with actual queue data."""
        # Standard departments
        standard_depts = ["general", "emergency", "pediatrics", "cardiology", "neurology", "orthopedics"]
        
        result = []
        for dept in standard_depts:
            if dept in self._department_stats:
                result.append(self._department_stats[dept].to_dict())
            else:
                # Return default status for departments not yet tracked
                result.append({
                    "department": dept,
                    "code": dept[:3].upper(),
                    "current_queue": 0,
                    "current_patients": 0,
                    "capacity": 30,
                    "crowd_level": "low",
                    "status": "normal",
                    "load_percentage": 0,
                    "avg_wait_minutes": 0,
                    "utilization_percent": 0,
                    "active_doctors": 2,
                    "spare_doctors_assigned": 0,
                    "teleconsult_redirects": 0
                })
        return result
    
    def get_hospital_overview(self) -> Dict:
        """Get overall hospital crowd status."""
        if not self._department_stats:
            return {
                "total_queue": 0,
                "total_capacity": 0,
                "overall_utilization": 0,
                "crowd_level": "low",
                "departments_at_capacity": 0,
                "teleconsult_queue": len(self._teleconsult_queue)
            }
        
        total_queue = sum(d.current_queue for d in self._department_stats.values())
        total_capacity = sum(d.capacity for d in self._department_stats.values())
        
        utilization = (total_queue / total_capacity * 100) if total_capacity > 0 else 0
        
        departments_critical = sum(
            1 for d in self._department_stats.values() 
            if d.crowd_level in [CrowdLevel.HIGH, CrowdLevel.CRITICAL]
        )
        
        overall_level = self.calculate_crowd_level(total_queue, total_capacity)
        
        return {
            "total_queue": total_queue,
            "total_capacity": total_capacity,
            "overall_utilization": round(utilization, 1),
            "crowd_level": overall_level.value,
            "departments_at_capacity": departments_critical,
            "total_departments": len(self._department_stats),
            "teleconsult_queue": len(self._teleconsult_queue),
            "recommendation": self._get_hospital_recommendation(overall_level)
        }
    
    def _get_hospital_recommendation(self, level: CrowdLevel) -> str:
        """Generate recommendation based on overall crowd level."""
        recommendations = {
            CrowdLevel.LOW: "Normal operations. All departments running smoothly.",
            CrowdLevel.MODERATE: "Moderate load. Monitor high-traffic departments.",
            CrowdLevel.HIGH: "High load. Consider activating spare doctor pool.",
            CrowdLevel.CRITICAL: "CRITICAL: Activate all spare doctors. Maximize teleconsult redirects."
        }
        return recommendations.get(level, "Monitor situation.")
    
    def add_to_teleconsult_queue(self, patient_data: Dict) -> Dict:
        """Add patient to teleconsult queue."""
        entry = {
            "patient_id": patient_data.get("patient_id"),
            "patient_name": patient_data.get("name"),
            "symptoms": patient_data.get("symptoms", []),
            "triage_score": patient_data.get("triage_score", 1),
            "queued_at": datetime.utcnow().isoformat(),
            "status": "waiting"
        }
        self._teleconsult_queue.append(entry)
        
        self._redirect_history.append({
            **entry,
            "redirected_from": patient_data.get("department", "GENERAL"),
            "reason": "crowd_management"
        })
        
        return {
            "success": True,
            "queue_position": len(self._teleconsult_queue),
            "estimated_wait": len(self._teleconsult_queue) * 10,  # 10 min per teleconsult
            "message": "Added to teleconsultation queue"
        }
    
    def get_teleconsult_queue(self) -> List[Dict]:
        """Get current teleconsult queue."""
        return self._teleconsult_queue
    
    def get_load_balancing_suggestions(self) -> List[Dict]:
        """
        Get suggestions for load balancing across departments.
        Simple greedy algorithm - move doctors from low-load to high-load.
        """
        suggestions = []
        
        # Sort departments by utilization
        sorted_depts = sorted(
            self._department_stats.values(),
            key=lambda d: d.utilization,
            reverse=True
        )
        
        for dept in sorted_depts:
            if dept.crowd_level == CrowdLevel.CRITICAL:
                # Find departments with low load
                donor_depts = [
                    d for d in sorted_depts 
                    if d.crowd_level == CrowdLevel.LOW and d.active_doctors > 1
                ]
                
                if donor_depts:
                    suggestions.append({
                        "action": "TRANSFER_DOCTOR",
                        "from_department": donor_depts[0].department,
                        "to_department": dept.department,
                        "reason": f"{dept.department} is at {dept.utilization:.0f}% capacity",
                        "priority": "high"
                    })
            
            elif dept.crowd_level == CrowdLevel.HIGH:
                suggestions.append({
                    "action": "ACTIVATE_SPARE",
                    "department": dept.department,
                    "reason": f"Queue length: {dept.current_queue}, utilization: {dept.utilization:.0f}%",
                    "priority": "medium"
                })
        
        return suggestions


# Singleton instance
_crowd_manager = None

def get_crowd_manager() -> CrowdManager:
    """Get the global crowd manager instance."""
    global _crowd_manager
    if _crowd_manager is None:
        _crowd_manager = CrowdManager()
    return _crowd_manager
