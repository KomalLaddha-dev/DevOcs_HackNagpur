"""
SmartCare AI Doctor Allocator
==============================
AI-powered automatic spare doctor assignment system.

Uses predictive analytics and rule-based AI to:
1. Predict queue surges before they happen
2. Auto-assign spare doctors to overloaded departments
3. Auto-release doctors when load decreases
4. Optimize doctor-patient matching based on specialty
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from app.services.spare_doctor_pool import get_spare_doctor_pool, DoctorStatus
from app.services.crowd_manager import get_crowd_manager
from app.services.priority_queue import get_priority_queue


@dataclass
class DepartmentMetrics:
    """Real-time department metrics for AI decision making."""
    department: str
    current_queue: int
    capacity: int
    utilization: float
    avg_wait_minutes: float
    critical_patients: int
    spare_doctors_assigned: int
    trend: str  # "increasing", "stable", "decreasing"
    predicted_queue_30min: int


@dataclass 
class AllocationDecision:
    """AI allocation decision with explanation."""
    action: str  # "assign", "release", "none"
    department: str
    doctor_id: Optional[int]
    doctor_name: Optional[str]
    confidence: float  # 0-1
    reason: str
    factors: List[str]


class AIDoctorAllocator:
    """
    AI-powered doctor allocation system.
    
    Decision Factors:
    =================
    1. Current utilization (weight: 0.3)
    2. Queue trend (weight: 0.25)
    3. Critical patient ratio (weight: 0.2)
    4. Average wait time (weight: 0.15)
    5. Time of day factor (weight: 0.1)
    
    Thresholds:
    - Assign: confidence > 0.7
    - Release: utilization < 0.5 and no critical patients
    """
    
    # AI Model Weights
    WEIGHTS = {
        "utilization": 0.30,
        "trend": 0.25,
        "critical_ratio": 0.20,
        "wait_time": 0.15,
        "time_factor": 0.10
    }
    
    # Thresholds
    ASSIGN_CONFIDENCE_THRESHOLD = 0.65
    RELEASE_UTILIZATION_THRESHOLD = 0.45
    CRITICAL_PATIENT_THRESHOLD = 2
    HIGH_WAIT_THRESHOLD_MINUTES = 30
    
    def __init__(self):
        self._queue_history: Dict[str, List[Tuple[datetime, int]]] = {}
        self._allocation_history: List[AllocationDecision] = []
        self._last_check: Dict[str, datetime] = {}
        
    def analyze_department(self, department: str) -> DepartmentMetrics:
        """Gather real-time metrics for a department."""
        pq = get_priority_queue()
        cm = get_crowd_manager()
        pool = get_spare_doctor_pool()
        
        # Get queue data
        queue_list = pq.get_queue_list()
        dept_queue = [p for p in queue_list if p.get("department", "").upper() == department.upper()]
        
        current_queue = len(dept_queue)
        
        # Count critical patients (severity 4-5)
        critical_count = sum(
            1 for p in dept_queue 
            if p.get("severity", "").upper() in ["CRITICAL", "HIGH"]
        )
        
        # Get department status from crowd manager
        dept_status = cm.get_department_status(department)
        capacity = dept_status.capacity if dept_status else 10
        active_doctors = dept_status.active_doctors if dept_status else 1
        
        # Calculate utilization
        utilization = min((current_queue / max(capacity, 1)) * 100, 100)
        
        # Calculate average wait
        if dept_queue:
            now = datetime.utcnow()
            waits = []
            for p in dept_queue:
                try:
                    checkin = datetime.fromisoformat(p.get("check_in_time", "").replace("Z", ""))
                    waits.append((now - checkin).total_seconds() / 60)
                except:
                    waits.append(0)
            avg_wait = statistics.mean(waits) if waits else 0
        else:
            avg_wait = 0
        
        # Get assigned spare doctors
        spare_assigned = len(pool.get_assigned_doctors(department))
        
        # Calculate trend
        trend = self._calculate_trend(department, current_queue)
        
        # Predict queue in 30 minutes
        predicted = self._predict_queue(department, current_queue, trend)
        
        # Store history
        if department not in self._queue_history:
            self._queue_history[department] = []
        self._queue_history[department].append((datetime.utcnow(), current_queue))
        # Keep only last 30 minutes of history
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        self._queue_history[department] = [
            (t, q) for t, q in self._queue_history[department] if t > cutoff
        ]
        
        return DepartmentMetrics(
            department=department,
            current_queue=current_queue,
            capacity=capacity,
            utilization=utilization,
            avg_wait_minutes=avg_wait,
            critical_patients=critical_count,
            spare_doctors_assigned=spare_assigned,
            trend=trend,
            predicted_queue_30min=predicted
        )
    
    def _calculate_trend(self, department: str, current: int) -> str:
        """Calculate queue trend based on history."""
        history = self._queue_history.get(department, [])
        
        if len(history) < 3:
            return "stable"
        
        # Get last 5 readings
        recent = [q for _, q in history[-5:]]
        
        if len(recent) < 2:
            return "stable"
        
        # Calculate slope
        diffs = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
        avg_diff = statistics.mean(diffs)
        
        if avg_diff > 0.5:
            return "increasing"
        elif avg_diff < -0.5:
            return "decreasing"
        return "stable"
    
    def _predict_queue(self, department: str, current: int, trend: str) -> int:
        """Predict queue size in 30 minutes using simple linear regression."""
        history = self._queue_history.get(department, [])
        
        if len(history) < 2:
            return current
        
        # Use trend to estimate
        if trend == "increasing":
            # Assume 1-2 patients every 10 minutes
            return current + 4
        elif trend == "decreasing":
            return max(0, current - 3)
        return current
    
    def calculate_assignment_score(self, metrics: DepartmentMetrics) -> Tuple[float, List[str]]:
        """
        Calculate AI score for spare doctor assignment.
        
        Returns (score 0-1, list of contributing factors)
        """
        factors = []
        score = 0.0
        
        # Factor 1: Utilization Score (0-1)
        util_score = min(metrics.utilization / 100, 1.0)
        if metrics.utilization >= 80:
            util_score = 1.0
            factors.append(f"High utilization: {metrics.utilization:.0f}%")
        elif metrics.utilization >= 60:
            util_score = 0.7
            factors.append(f"Moderate utilization: {metrics.utilization:.0f}%")
        score += util_score * self.WEIGHTS["utilization"]
        
        # Factor 2: Trend Score (0-1)
        if metrics.trend == "increasing":
            trend_score = 1.0
            factors.append("Queue is growing rapidly")
        elif metrics.trend == "stable":
            trend_score = 0.5
        else:
            trend_score = 0.2
        score += trend_score * self.WEIGHTS["trend"]
        
        # Factor 3: Critical Patient Ratio (0-1)
        if metrics.current_queue > 0:
            critical_ratio = metrics.critical_patients / metrics.current_queue
        else:
            critical_ratio = 0
        
        if metrics.critical_patients >= self.CRITICAL_PATIENT_THRESHOLD:
            factors.append(f"{metrics.critical_patients} critical patients in queue")
            critical_score = 1.0
        else:
            critical_score = critical_ratio
        score += critical_score * self.WEIGHTS["critical_ratio"]
        
        # Factor 4: Wait Time Score (0-1)
        if metrics.avg_wait_minutes >= self.HIGH_WAIT_THRESHOLD_MINUTES:
            wait_score = 1.0
            factors.append(f"Long average wait: {metrics.avg_wait_minutes:.0f} min")
        else:
            wait_score = metrics.avg_wait_minutes / self.HIGH_WAIT_THRESHOLD_MINUTES
        score += wait_score * self.WEIGHTS["wait_time"]
        
        # Factor 5: Time of Day (0-1)
        hour = datetime.utcnow().hour
        # Peak hours: 9-12, 16-19
        if 9 <= hour <= 12 or 16 <= hour <= 19:
            time_score = 0.8
            factors.append("Peak hours - higher demand expected")
        elif 6 <= hour <= 22:
            time_score = 0.5
        else:
            time_score = 0.2
        score += time_score * self.WEIGHTS["time_factor"]
        
        # Bonus: Predicted surge
        if metrics.predicted_queue_30min > metrics.current_queue + 3:
            score += 0.1
            factors.append(f"Predicted surge: {metrics.predicted_queue_30min} patients in 30min")
        
        return min(score, 1.0), factors
    
    def make_allocation_decision(self, department: str) -> AllocationDecision:
        """
        AI decision engine for doctor allocation.
        
        Returns recommendation with confidence and explanation.
        """
        pool = get_spare_doctor_pool()
        metrics = self.analyze_department(department)
        
        # Calculate assignment score
        score, factors = self.calculate_assignment_score(metrics)
        
        # Check for release condition first
        if (metrics.utilization < self.RELEASE_UTILIZATION_THRESHOLD * 100 and 
            metrics.critical_patients == 0 and
            metrics.spare_doctors_assigned > 0):
            
            assigned = pool.get_assigned_doctors(department)
            if assigned:
                return AllocationDecision(
                    action="release",
                    department=department,
                    doctor_id=assigned[0].doctor_id,
                    doctor_name=assigned[0].name,
                    confidence=0.9,
                    reason=f"Low utilization ({metrics.utilization:.0f}%) - releasing spare doctor",
                    factors=[f"Utilization below {self.RELEASE_UTILIZATION_THRESHOLD*100:.0f}%", "No critical patients"]
                )
        
        # Check for assignment condition
        max_spare = 3  # from config
        if (score >= self.ASSIGN_CONFIDENCE_THRESHOLD and 
            metrics.spare_doctors_assigned < max_spare):
            
            # Find best matching doctor
            available = pool.get_available_doctors(department)
            if not available:
                available = pool.get_available_doctors("GENERAL")
            
            if available:
                # Pick doctor with most remaining capacity
                best_doctor = max(available, key=lambda d: d.max_patients - d.patients_seen)
                
                return AllocationDecision(
                    action="assign",
                    department=department,
                    doctor_id=best_doctor.doctor_id,
                    doctor_name=best_doctor.name,
                    confidence=score,
                    reason=f"High load detected - recommending spare doctor assignment",
                    factors=factors
                )
            else:
                return AllocationDecision(
                    action="none",
                    department=department,
                    doctor_id=None,
                    doctor_name=None,
                    confidence=score,
                    reason="No spare doctors available in pool",
                    factors=factors + ["All spare doctors already assigned"]
                )
        
        return AllocationDecision(
            action="none",
            department=department,
            doctor_id=None,
            doctor_name=None,
            confidence=score,
            reason="Current staffing is adequate",
            factors=factors if factors else ["All metrics within normal range"]
        )
    
    def auto_allocate_all_departments(self) -> List[Dict]:
        """
        Run AI allocation check for all departments.
        Executes assignments automatically.
        """
        departments = ["general", "emergency", "pediatrics", "cardiology", "orthopedics", "neurology"]
        results = []
        pool = get_spare_doctor_pool()
        
        for dept in departments:
            decision = self.make_allocation_decision(dept)
            
            result = {
                "department": dept,
                "action": decision.action,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "factors": decision.factors,
                "executed": False
            }
            
            # Execute decision if confidence is high enough
            if decision.action == "assign" and decision.doctor_id:
                assignment = pool.assign_doctor(
                    decision.doctor_id,
                    dept,
                    f"AI Auto-Assignment: {decision.reason}",
                    "ai_system"
                )
                if assignment and assignment.get("success"):
                    result["executed"] = True
                    result["doctor_assigned"] = decision.doctor_name
                    
            elif decision.action == "release" and decision.doctor_id:
                release = pool.release_doctor(
                    decision.doctor_id,
                    f"AI Auto-Release: {decision.reason}",
                    "ai_system"
                )
                if release and release.get("success"):
                    result["executed"] = True
                    result["doctor_released"] = decision.doctor_name
            
            results.append(result)
            self._allocation_history.append(decision)
        
        return results
    
    def get_ai_insights(self) -> Dict:
        """Get AI system insights and statistics."""
        pool = get_spare_doctor_pool()
        
        total_available = len(pool.get_available_doctors())
        total_assigned = len(pool.get_assigned_doctors())
        
        # Analyze all departments
        departments = ["general", "emergency", "pediatrics", "cardiology", "orthopedics", "neurology"]
        dept_analysis = []
        
        for dept in departments:
            metrics = self.analyze_department(dept)
            score, factors = self.calculate_assignment_score(metrics)
            
            dept_analysis.append({
                "department": dept,
                "utilization": metrics.utilization,
                "queue_size": metrics.current_queue,
                "critical_patients": metrics.critical_patients,
                "trend": metrics.trend,
                "predicted_30min": metrics.predicted_queue_30min,
                "spare_doctors": metrics.spare_doctors_assigned,
                "ai_score": round(score, 2),
                "needs_attention": score >= self.ASSIGN_CONFIDENCE_THRESHOLD
            })
        
        # Recent decisions
        recent_decisions = [
            {
                "action": d.action,
                "department": d.department,
                "confidence": d.confidence,
                "reason": d.reason
            }
            for d in self._allocation_history[-10:]
        ]
        
        return {
            "system_status": "active",
            "spare_pool_summary": {
                "available": total_available,
                "assigned": total_assigned,
                "total": total_available + total_assigned
            },
            "department_analysis": dept_analysis,
            "high_priority_departments": [
                d["department"] for d in dept_analysis if d["needs_attention"]
            ],
            "recent_ai_decisions": recent_decisions,
            "model_config": {
                "weights": self.WEIGHTS,
                "assign_threshold": self.ASSIGN_CONFIDENCE_THRESHOLD,
                "release_threshold": self.RELEASE_UTILIZATION_THRESHOLD
            }
        }

    def calculate_wait_time_impact(self, department: str) -> Dict:
        """
        Calculate wait time impact when critical patients arrive.
        
        WAIT TIME PROTECTION ALGORITHM:
        ================================
        When critical patients jump the queue, they should NOT increase
        wait times for existing patients. Instead, spare doctors should
        be assigned to maintain committed wait times.
        
        Formula:
        - Original wait for patient N = N * avg_time_per_patient / num_doctors
        - After K critical patients arrive (jump to front):
          Patient N becomes position (N + K)
          New wait = (N + K) * avg_time_per_patient / num_doctors
        
        To maintain original wait time:
        - Need extra doctors = K * avg_time / original_wait
        - Or: extra_doctors_needed = ceil(K / current_doctors)
        """
        pq = get_priority_queue()
        cm = get_crowd_manager()
        pool = get_spare_doctor_pool()
        
        queue_list = pq.get_queue_list()
        dept_queue = [p for p in queue_list if p.get("department", "").upper() == department.upper()]
        
        # Separate critical and non-critical patients
        critical_patients = [p for p in dept_queue if p.get("severity", "").upper() in ["CRITICAL", "HIGH"]]
        regular_patients = [p for p in dept_queue if p.get("severity", "").upper() not in ["CRITICAL", "HIGH"]]
        
        num_critical = len(critical_patients)
        num_regular = len(regular_patients)
        total_queue = len(dept_queue)
        
        # Get current doctor count
        dept_status = cm.get_department_status(department)
        active_doctors = dept_status.active_doctors if dept_status else 1
        spare_assigned = len(pool.get_assigned_doctors(department))
        total_doctors = active_doctors + spare_assigned
        
        # Average time per patient (minutes)
        AVG_CONSULTATION_TIME = 15
        
        # Calculate wait times
        if total_queue == 0:
            return {
                "department": department,
                "impact": "none",
                "critical_patients": 0,
                "regular_patients": 0,
                "extra_doctors_needed": 0,
                "wait_time_protected": True,
                "explanation": "No patients in queue"
            }
        
        # Calculate original wait time for the last regular patient (worst case)
        if num_regular > 0:
            # Original position before critical patients arrived
            original_position = num_regular
            original_wait = (original_position * AVG_CONSULTATION_TIME) / total_doctors
            
            # New position after critical patients jump ahead
            new_position = num_critical + num_regular  # Critical patients are at front
            new_wait = (new_position * AVG_CONSULTATION_TIME) / total_doctors
            
            wait_increase = new_wait - original_wait
            wait_increase_percent = (wait_increase / max(original_wait, 1)) * 100
        else:
            original_wait = 0
            new_wait = 0
            wait_increase = 0
            wait_increase_percent = 0
        
        # Calculate extra doctors needed to maintain original wait times
        # Formula: To serve K extra patients in same time, need K/current_doctors extra doctors
        if num_critical > 0 and total_doctors > 0:
            # Each doctor handles ~4 patients per hour (15 min each)
            # Extra doctors needed = critical_patients / doctors_per_critical_patient
            extra_doctors_needed = max(1, (num_critical + total_doctors - 1) // total_doctors)
            
            # More precise: to maintain same wait, need enough doctors to serve critical patients
            # without delaying regulars
            extra_doctors_needed = min(extra_doctors_needed, 3)  # Cap at max spare
        else:
            extra_doctors_needed = 0
        
        # Check if we can protect wait times
        available_spare = len(pool.get_available_doctors(department)) + len(pool.get_available_doctors("GENERAL"))
        can_protect = available_spare >= extra_doctors_needed
        
        return {
            "department": department,
            "total_queue": total_queue,
            "critical_patients": num_critical,
            "regular_patients": num_regular,
            "current_doctors": total_doctors,
            "spare_doctors_assigned": spare_assigned,
            "original_wait_minutes": round(original_wait, 1),
            "new_wait_without_protection": round(new_wait, 1),
            "wait_increase_minutes": round(wait_increase, 1),
            "wait_increase_percent": round(wait_increase_percent, 1),
            "extra_doctors_needed": extra_doctors_needed,
            "available_spare_doctors": available_spare,
            "can_protect_wait_times": can_protect,
            "wait_time_protected": spare_assigned >= extra_doctors_needed,
            "recommendation": self._get_wait_protection_recommendation(
                num_critical, extra_doctors_needed, available_spare, spare_assigned
            )
        }
    
    def _get_wait_protection_recommendation(
        self, 
        critical_count: int, 
        doctors_needed: int, 
        available: int,
        already_assigned: int
    ) -> str:
        """Generate recommendation for wait time protection."""
        if critical_count == 0:
            return "No critical patients - wait times stable"
        
        if already_assigned >= doctors_needed:
            return f"Wait times protected - {already_assigned} spare doctor(s) already handling surge"
        
        shortfall = doctors_needed - already_assigned
        if available >= shortfall:
            return f"RECOMMEND: Assign {shortfall} more spare doctor(s) to protect wait times"
        elif available > 0:
            return f"WARNING: Need {shortfall} doctors but only {available} available - partial protection possible"
        else:
            return f"ALERT: No spare doctors available - wait times will increase by {critical_count * 15 // max(1, already_assigned + 1)} minutes"

    def protect_wait_times(self, department: str) -> Dict:
        """
        Automatically assign spare doctors to protect wait times when critical patients arrive.
        
        This is the main entry point for the Wait Time Protection feature.
        """
        pool = get_spare_doctor_pool()
        
        # Analyze impact
        impact = self.calculate_wait_time_impact(department)
        
        result = {
            "department": department,
            "impact_analysis": impact,
            "actions_taken": [],
            "wait_time_protected": impact["wait_time_protected"]
        }
        
        # If wait times already protected, no action needed
        if impact["wait_time_protected"]:
            result["message"] = "Wait times already protected"
            return result
        
        # Calculate how many doctors to assign
        doctors_to_assign = impact["extra_doctors_needed"] - impact["spare_doctors_assigned"]
        
        if doctors_to_assign <= 0:
            result["message"] = "Sufficient doctors already assigned"
            return result
        
        # Try to assign doctors
        assigned_count = 0
        for _ in range(doctors_to_assign):
            # Try specialty match first, then general
            available = pool.get_available_doctors(department)
            if not available:
                available = pool.get_available_doctors("GENERAL")
            
            if not available:
                break
            
            doctor = available[0]
            assignment = pool.assign_doctor(
                doctor.doctor_id,
                department,
                f"Wait Time Protection: {impact['critical_patients']} critical patients in queue",
                "ai_wait_protection"
            )
            
            if assignment and assignment.get("success"):
                assigned_count += 1
                result["actions_taken"].append({
                    "action": "assigned",
                    "doctor_id": doctor.doctor_id,
                    "doctor_name": doctor.name,
                    "reason": "Wait time protection"
                })
                
                # Log the decision
                self._allocation_history.append(AllocationDecision(
                    action="assign",
                    department=department,
                    doctor_id=doctor.doctor_id,
                    doctor_name=doctor.name,
                    confidence=0.95,
                    reason=f"Wait Time Protection - {impact['critical_patients']} critical patients",
                    factors=[
                        f"Critical patients: {impact['critical_patients']}",
                        f"Wait increase prevented: {impact['wait_increase_minutes']:.0f} min",
                        "Protecting existing patient wait times"
                    ]
                ))
        
        result["doctors_assigned"] = assigned_count
        result["doctors_requested"] = doctors_to_assign
        result["wait_time_protected"] = assigned_count >= doctors_to_assign
        
        if assigned_count >= doctors_to_assign:
            result["message"] = f"Wait times protected! Assigned {assigned_count} spare doctor(s)"
        elif assigned_count > 0:
            result["message"] = f"Partial protection: Assigned {assigned_count}/{doctors_to_assign} doctors needed"
        else:
            result["message"] = "Could not protect wait times - no spare doctors available"
        
        return result

    def auto_protect_all_departments(self) -> Dict:
        """
        Run wait time protection for all departments automatically.
        
        This should be called whenever critical patients are added to the queue.
        """
        departments = ["general", "emergency", "pediatrics", "cardiology", "orthopedics", "neurology"]
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "departments_checked": len(departments),
            "departments_protected": 0,
            "total_doctors_assigned": 0,
            "details": []
        }
        
        for dept in departments:
            protection_result = self.protect_wait_times(dept)
            results["details"].append(protection_result)
            
            if protection_result.get("wait_time_protected"):
                results["departments_protected"] += 1
            
            results["total_doctors_assigned"] += len(protection_result.get("actions_taken", []))
        
        return results


# Singleton
_ai_allocator = None

def get_ai_allocator() -> AIDoctorAllocator:
    """Get the global AI allocator instance."""
    global _ai_allocator
    if _ai_allocator is None:
        _ai_allocator = AIDoctorAllocator()
    return _ai_allocator
