"""
SmartCare Comprehensive Queue API
==================================
All-in-one API for queue, triage, crowd management, and emergencies.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services.triage_engine import TriageEngine, triage_patient
from app.services.priority_queue import get_priority_queue
from app.services.crowd_manager import get_crowd_manager
from app.services.spare_doctor_pool import get_spare_doctor_pool
from app.services.emergency_override import get_override_system, OverrideReason
from app.services.ai_doctor_allocator import get_ai_allocator
from app.services.activity_logger import get_activity_logger

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class TriageRequest(BaseModel):
    symptoms: List[str] = Field(..., example=["fever", "cough"])
    description: str = Field("", example="High fever for 2 days")
    age: int = Field(..., ge=0, le=120, example=45)
    chronic_conditions: List[str] = Field(default=[], example=["diabetes"])
    duration_hours: int = Field(default=0, ge=0)
    is_emergency: bool = Field(default=False)
    self_severity: int = Field(default=5, ge=1, le=10)


class CheckInRequest(BaseModel):
    patient_id: int
    patient_name: str
    symptoms: List[str]
    description: str = ""
    age: int
    chronic_conditions: List[str] = []
    duration_hours: int = 0
    self_severity: int = 5
    department: str = "GENERAL"


class EmergencyRequest(BaseModel):
    queue_entry_id: int
    patient_id: int
    patient_name: str
    reason_code: str
    reason_notes: str = ""
    boost_amount: Optional[int] = None


class DepartmentUpdate(BaseModel):
    department: str
    current_queue: int
    active_doctors: int
    spare_doctors: int = 0


# =============================================================================
# TRIAGE ENDPOINT
# =============================================================================

@router.post("/triage/assess")
async def assess_patient(request: TriageRequest):
    """
    AI Triage Assessment
    
    Analyzes symptoms and returns:
    - Severity score (1-5)
    - Recommended action
    - Wait time estimate
    - Teleconsult eligibility
    - Full explanation
    """
    result = triage_patient(
        symptoms=request.symptoms,
        description=request.description,
        age=request.age,
        chronic_conditions=request.chronic_conditions,
        duration_hours=request.duration_hours,
        is_emergency=request.is_emergency,
        self_severity=request.self_severity
    )
    return {"success": True, "triage": result}


# =============================================================================
# QUEUE ENDPOINTS
# =============================================================================

@router.post("/checkin")
async def checkin_patient(request: CheckInRequest):
    """Check in patient - runs triage and adds to priority queue."""
    # Triage
    triage_result = triage_patient(
        symptoms=request.symptoms,
        description=request.description,
        age=request.age,
        chronic_conditions=request.chronic_conditions,
        duration_hours=request.duration_hours,
        self_severity=request.self_severity
    )
    
    pq = get_priority_queue()
    cm = get_crowd_manager()
    
    # Normalize department to lowercase
    department = request.department.lower() if request.department else "general"
    
    entry_id = int(datetime.utcnow().timestamp() * 1000) % 1000000
    age_factor = TriageEngine.get_age_risk_factor(request.age)
    chronic_boost, _ = TriageEngine.calculate_chronic_boost(request.chronic_conditions)
    
    priority = pq.push(
        patient_id=request.patient_id,
        entry_id=entry_id,
        triage_score=triage_result["triage_score"],
        age_factor=age_factor,
        chronic_factor=chronic_boost
    )
    
    # Store patient info for display
    pq._patient_info[entry_id] = {
        "name": request.patient_name,
        "age": request.age,
        "symptoms": request.symptoms,
        "chronic_conditions": request.chronic_conditions,
        "department": department,
        "severity": triage_result["severity_level"],
        "explanation": triage_result["explanation"]
    }
    
    queue_list = pq.get_queue_list()
    position = next((q["position"] for q in queue_list if q["entry_id"] == entry_id), 1)
    
    # Count patients in this department
    dept_patient_count = len([p for p in queue_list if p.get("department", "").lower() == department])
    
    # Update department status with actual queue count
    dept_status = cm.update_department_status(
        department=department,
        current_queue=dept_patient_count,
        active_doctors=2  # Default doctors per department
    )
    
    wait = cm.calculate_expected_wait(
        position=position,
        triage_score=triage_result["triage_score"],
        active_doctors=dept_status.active_doctors if dept_status else 1
    )
    
    teleconsult = cm.should_redirect_to_teleconsult(
        triage_score=triage_result["triage_score"],
        crowd_level=dept_status.crowd_level if dept_status else "low"
    )
    
    # AUTO WAIT TIME PROTECTION: If critical patient, auto-assign spare doctors
    wait_protection = None
    if triage_result["severity_level"].upper() in ["CRITICAL", "HIGH"]:
        allocator = get_ai_allocator()
        wait_protection = allocator.protect_wait_times(department)
    
    # Log patient check-in activity
    logger = get_activity_logger()
    logger.log_patient_checkin(
        patient_name=request.patient_name,
        patient_id=request.patient_id,
        entry_id=entry_id,
        token=f"TKN-{entry_id}",
        department=department,
        symptoms=request.symptoms,
        triage_score=triage_result["triage_score"],
        severity_level=triage_result["severity_level"],
        priority_score=round(priority, 3),
        wait_minutes=wait.get("estimated_minutes", 0)
    )
    
    # Run AI auto-allocation check after check-in
    allocator = get_ai_allocator()
    ai_result = allocator.auto_allocate_all_departments()
    ai_actions = [r for r in ai_result if r.get("executed")]
    
    return {
        "success": True,
        "entry_id": entry_id,
        "token": f"TKN-{entry_id}",
        "position": position,
        "priority_score": round(priority, 3),
        "triage": triage_result,
        "triage_score_10": triage_result["triage_score"],  # Already 1-10 scale
        "wait_estimate": wait,
        "teleconsult": teleconsult,
        "wait_time_protection": wait_protection,
        "department": department,
        "ai_actions_taken": len(ai_actions)
    }


@router.get("/status")
async def get_queue_status():
    """Get quick queue status overview for display."""
    pq = get_priority_queue()
    cm = get_crowd_manager()
    pool = get_spare_doctor_pool()
    
    stats = pq.get_stats()
    pool_status = pool.get_pool_status()
    
    # Get queue by department from actual patient data
    queue_list = pq.get_queue_list()
    dept_counts = {}
    for patient in queue_list:
        dept = patient.get("department", "general").lower()
        if dept not in dept_counts:
            dept_counts[dept] = {"count": 0, "critical": 0}
        dept_counts[dept]["count"] += 1
        if patient.get("triage_score", 3) >= 5:
            dept_counts[dept]["critical"] += 1
    
    # Standard departments
    departments = ["general", "emergency", "pediatrics", "cardiology", "neurology", "orthopedics"]
    dept_list = []
    total_doctors = 0
    
    for dept in departments:
        dept_status = cm.get_department_status(dept)
        active_docs = dept_status.active_doctors if dept_status else 2
        total_doctors += active_docs
        queue_count = dept_counts.get(dept, {}).get("count", 0)
        
        dept_list.append({
            "name": dept,
            "queue_count": queue_count,
            "crowd_level": "low" if queue_count < 10 else "moderate" if queue_count < 20 else "high",
            "avg_wait": round(queue_count * 8 / max(active_docs, 1), 0)
        })
    
    total_queue = stats.get("total_patients", 0)
    avg_wait = round(total_queue * 8 / max(total_doctors, 1), 1) if total_queue > 0 else 0
    
    return {
        "success": True,
        "total_in_queue": total_queue,
        "avg_wait_minutes": avg_wait,
        "total_doctors": total_doctors,
        "spare_doctors_available": pool_status.get("available", 0),
        "critical_patients": stats.get("critical_count", 0),
        "departments": dept_list
    }


@router.get("/list")
async def get_queue_list(department: Optional[str] = None, limit: int = 50):
    """Get full priority queue, optionally filtered by department."""
    pq = get_priority_queue()
    pool = get_spare_doctor_pool()
    
    queue_list = pq.get_queue_list()
    
    # Filter by department if specified
    if department:
        queue_list = [p for p in queue_list if p.get("department", "").lower() == department.lower()]
    
    # Limit results
    queue_list = queue_list[:limit]
    
    # Calculate expected wait for each patient
    cm = get_crowd_manager()
    for patient in queue_list:
        dept = patient.get("department", "general")
        dept_status = cm.get_department_status(dept)
        active_docs = dept_status.active_doctors if dept_status else 2
        patient["expected_wait_minutes"] = cm.calculate_expected_wait(
            patient["position"], patient["triage_score"], active_docs
        )
        patient["teleconsult_eligible"] = patient.get("triage_score", 3) <= 2
    
    stats = pq.get_stats()
    
    # Check if spare doctors should be activated
    total_queue = stats.get("total_patients", 0)
    if total_queue > 10:  # Threshold for spare doctor activation
        activation = pool.should_activate_spare_doctors("general", total_queue, 15, len(pool.get_assigned_doctors()))
        if activation.get("should_activate"):
            stats["spare_doctor_alert"] = {
                "needed": True,
                "reason": activation.get("reason", "High patient load"),
                "recommended_count": activation.get("recommended_count", 1)
            }
    
    return {
        "success": True,
        "queue": queue_list,
        "stats": stats
    }


@router.get("/position/{entry_id}")
async def get_position(entry_id: int):
    """Get patient's queue position."""
    pq = get_priority_queue()
    cm = get_crowd_manager()
    
    for item in pq.get_queue_list():
        if item["entry_id"] == entry_id:
            wait = cm.calculate_expected_wait(item["position"], item["triage_score"])
            return {"success": True, "position": item["position"], "wait": wait, "item": item}
    
    raise HTTPException(404, "Not found")


@router.post("/next")
async def call_next(department: Optional[str] = None):
    """Call next patient from queue."""
    pq = get_priority_queue()
    
    # Check if there's already a patient being seen
    current = pq.get_current_patient(department or "general")
    if current:
        return {
            "success": False, 
            "message": "Complete current patient first",
            "current_patient": current
        }
    
    # Get queue list to find next patient (optionally filtered by department)
    queue_list = pq.get_queue_list()
    
    if department:
        queue_list = [p for p in queue_list if p.get("department", "").lower() == department.lower()]
    
    if not queue_list:
        return {"success": False, "message": "No patients in queue" + (f" for {department}" if department else "")}
    
    # Get the first (highest priority) patient
    next_patient = queue_list[0]
    entry_id = next_patient["entry_id"]
    
    # Remove from queue
    pq.remove(entry_id)
    
    # Build patient data
    patient_data = {
        "entry_id": str(next_patient.get("entry_id", "")),
        "patient_name": next_patient.get("patient_name", f"Patient #{next_patient.get('patient_id', '')}"),
        "symptoms": next_patient.get("symptoms", []),
        "chronic_conditions": next_patient.get("chronic_conditions", []),
        "severity": next_patient.get("severity", "MEDIUM"),
        "triage_explanation": next_patient.get("triage_explanation", []),
        "check_in_time": next_patient.get("check_in_time", ""),
        "age": next_patient.get("age", 0),
        "department": next_patient.get("department", "general"),
        "priority_score": next_patient.get("priority_score", 0)
    }
    
    # Set as current patient being seen
    pq.set_current_patient(department or "general", patient_data)
    
    # Also remove from patient_info
    if entry_id in pq._patient_info:
        del pq._patient_info[entry_id]
    
    return {
        "success": True,
        "patient": patient_data
    }


@router.get("/current")
async def get_current_patient(department: Optional[str] = None):
    """Get the current patient being seen for a department."""
    pq = get_priority_queue()
    patient = pq.get_current_patient(department or "general")
    return {
        "success": True,
        "patient": patient,
        "has_patient": patient is not None
    }


@router.post("/complete")
async def complete_patient(department: Optional[str] = None):
    """Mark current patient consultation as complete."""
    pq = get_priority_queue()
    cleared = pq.clear_current_patient(department or "general")
    return {
        "success": cleared,
        "message": "Patient consultation completed" if cleared else "No patient was being seen"
    }


@router.post("/recalculate")
async def recalculate():
    """Recalculate all priorities."""
    pq = get_priority_queue()
    count = pq.recalculate_all_priorities()
    return {"success": True, "updated": count}


# =============================================================================
# CROWD MANAGEMENT
# =============================================================================

@router.get("/crowd/status")
async def crowd_status():
    """Hospital crowd overview with real queue data."""
    cm = get_crowd_manager()
    pq = get_priority_queue()
    
    # Get actual queue counts by department
    queue_list = pq.get_queue_list()
    dept_counts = {}
    for patient in queue_list:
        dept = patient.get("department", "general").lower()
        if dept not in dept_counts:
            dept_counts[dept] = 0
        dept_counts[dept] += 1
    
    # Update department statuses with real counts
    standard_depts = ["general", "emergency", "pediatrics", "cardiology", "neurology", "orthopedics"]
    for dept in standard_depts:
        count = dept_counts.get(dept, 0)
        cm.update_department_status(
            department=dept,
            current_queue=count,
            active_doctors=2  # Default
        )
    
    return {
        "success": True,
        "overview": cm.get_hospital_overview(),
        "departments": cm.get_all_departments_status()
    }


@router.post("/crowd/department")
async def update_department(request: DepartmentUpdate):
    """Update department status."""
    cm = get_crowd_manager()
    status = cm.update_department_status(
        request.department, request.current_queue, 
        request.active_doctors, request.spare_doctors
    )
    return {"success": True, "status": status.to_dict()}


@router.get("/crowd/suggestions")
async def load_suggestions():
    """Get load balancing suggestions."""
    cm = get_crowd_manager()
    return {"success": True, "suggestions": cm.get_load_balancing_suggestions()}


@router.get("/crowd/teleconsult")
async def teleconsult_queue():
    """Get teleconsult queue."""
    cm = get_crowd_manager()
    return {"success": True, "queue": cm.get_teleconsult_queue()}


@router.post("/crowd/redirect-teleconsult")
async def redirect_teleconsult(data: dict):
    """Redirect patient to teleconsult."""
    cm = get_crowd_manager()
    return cm.add_to_teleconsult_queue(data)


# =============================================================================
# SPARE DOCTOR POOL
# =============================================================================

@router.get("/doctors/spare")
async def spare_pool():
    """Spare doctor pool status with all doctors."""
    pool = get_spare_doctor_pool()
    all_doctors = [doc.to_dict() for doc in pool._pool.values()]
    available = pool.get_available_doctors()
    assigned = pool.get_assigned_doctors()
    
    return {
        "success": True,
        "doctors": all_doctors,
        "available_count": len(available),
        "assigned_count": len(assigned),
        "status": pool.get_pool_status(),
        "specialties": pool.get_specialties_available()
    }


@router.get("/doctors/spare/available")
async def available_doctors(specialty: Optional[str] = None):
    """Available spare doctors."""
    pool = get_spare_doctor_pool()
    doctors = pool.get_available_doctors(specialty)
    return {"success": True, "doctors": [d.to_dict() for d in doctors]}


class AssignDoctorRequest(BaseModel):
    doctor_id: int
    department: str
    reason: str = "Manual assignment"

@router.post("/doctors/spare/assign")
async def assign_doctor(request: AssignDoctorRequest):
    """Assign spare doctor to a department."""
    pool = get_spare_doctor_pool()
    logger = get_activity_logger()
    
    result = pool.assign_doctor(request.doctor_id, request.department, request.reason, "admin")
    if not result:
        raise HTTPException(404, "Doctor not found or not available")
    
    if result.get("success"):
        doctor = result.get("doctor", {})
        logger.log_doctor_assigned(
            doctor_id=request.doctor_id,
            doctor_name=doctor.get("name", f"Doctor #{request.doctor_id}"),
            department=request.department,
            reason=request.reason,
            initiated_by="admin"
        )
    
    return {"success": True, **result}


class ReleaseDoctorRequest(BaseModel):
    doctor_id: int
    reason: str = "Manual release"

@router.post("/doctors/spare/release")
async def release_doctor(request: ReleaseDoctorRequest):
    """Release spare doctor from assignment."""
    pool = get_spare_doctor_pool()
    logger = get_activity_logger()
    
    # Get doctor info before release
    doctor_info = pool._pool.get(request.doctor_id)
    old_department = doctor_info.assigned_department if doctor_info else "unknown"
    
    result = pool.release_doctor(request.doctor_id, request.reason, "admin")
    if not result:
        raise HTTPException(404, "Doctor not found or not assigned")
    
    if result.get("success"):
        doctor = result.get("doctor", {})
        logger.log_doctor_released(
            doctor_id=request.doctor_id,
            doctor_name=doctor.get("name", f"Doctor #{request.doctor_id}"),
            department=old_department,
            reason=request.reason,
            initiated_by="admin"
        )
    
    return {"success": True, **result}


@router.get("/doctors/spare/logs")
async def spare_logs(limit: int = 50):
    """Spare doctor assignment logs."""
    pool = get_spare_doctor_pool()
    return {"success": True, "logs": pool.get_assignment_logs(limit)}


# =============================================================================
# EMERGENCY OVERRIDE
# =============================================================================

@router.post("/emergency/escalate")
async def emergency_escalate(
    request: EmergencyRequest,
    auth_id: int = Query(...),
    auth_name: str = Query(...),
    auth_role: str = Query(...)
):
    """Emergency escalate to top of queue."""
    system = get_override_system()
    try:
        reason = OverrideReason[request.reason_code.upper()]
    except:
        reason = OverrideReason.OTHER
    
    result = system.emergency_escalate(
        request.queue_entry_id, request.patient_id, request.patient_name,
        auth_id, auth_name, auth_role, reason, request.reason_notes
    )
    if not result["success"]:
        raise HTTPException(403, result.get("error"))
    return result


@router.post("/emergency/boost")
async def priority_boost(
    request: EmergencyRequest,
    auth_id: int = Query(...),
    auth_name: str = Query(...),
    auth_role: str = Query(...)
):
    """Boost patient priority."""
    system = get_override_system()
    try:
        reason = OverrideReason[request.reason_code.upper()]
    except:
        reason = OverrideReason.OTHER
    
    result = system.priority_boost(
        request.queue_entry_id, request.patient_id, request.patient_name,
        request.boost_amount or 1, auth_id, auth_name, auth_role, reason, request.reason_notes
    )
    if not result["success"]:
        raise HTTPException(403, result.get("error"))
    return result


@router.get("/emergency/logs")
async def override_logs(limit: int = 100):
    """Emergency override audit logs."""
    system = get_override_system()
    return {"success": True, "logs": system.get_override_logs(limit)}


@router.get("/emergency/stats")
async def override_stats():
    """Override statistics."""
    system = get_override_system()
    return {"success": True, "stats": system.get_override_stats()}


# =============================================================================
# DEMO/SEED ENDPOINTS
# =============================================================================

@router.post("/demo/seed")
async def seed_demo_data():
    """Seed demo data for hackathon demonstration."""
    import random
    from datetime import datetime, timedelta
    
    DEMO_PATIENTS = [
        {"name": "John Smith", "age": 72, "symptoms": ["chest_pain", "shortness_of_breath"], 
         "chronic": ["heart_disease", "diabetes"], "dept": "cardiology", "duration": 1},
        {"name": "Maria Garcia", "age": 35, "symptoms": ["severe_bleeding", "abdominal_pain"], 
         "chronic": [], "dept": "emergency", "duration": 1},
        {"name": "Baby Emma", "age": 2, "symptoms": ["high_fever", "difficulty_breathing"], 
         "chronic": ["asthma"], "dept": "pediatrics", "duration": 4},
        {"name": "Robert Johnson", "age": 45, "symptoms": ["headache", "fatigue"], 
         "chronic": [], "dept": "general", "duration": 24},
        {"name": "Sarah Davis", "age": 28, "symptoms": ["cough", "sore_throat"], 
         "chronic": [], "dept": "general", "duration": 48},
        {"name": "Michael Brown", "age": 65, "symptoms": ["confusion", "severe_headache"], 
         "chronic": ["hypertension", "diabetes"], "dept": "neurology", "duration": 2},
        {"name": "Jennifer Lee", "age": 55, "symptoms": ["joint_pain", "swelling"], 
         "chronic": ["arthritis"], "dept": "orthopedics", "duration": 72},
        {"name": "David Martinez", "age": 40, "symptoms": ["nausea", "vomiting"], 
         "chronic": [], "dept": "general", "duration": 6},
    ]
    
    pq = get_priority_queue()
    cm = get_crowd_manager()
    results = []
    
    for i, p in enumerate(DEMO_PATIENTS):
        triage_result = triage_patient(
            symptoms=p["symptoms"],
            age=p["age"],
            chronic_conditions=p["chronic"],
            duration_hours=p["duration"]
        )
        
        entry_id = int(datetime.utcnow().timestamp() * 1000) % 1000000 + i
        age_factor = TriageEngine.get_age_risk_factor(p["age"])
        chronic_boost, _ = TriageEngine.calculate_chronic_boost(p["chronic"])
        
        priority = pq.push(
            patient_id=100 + i,
            entry_id=entry_id,
            triage_score=triage_result["triage_score"],
            age_factor=age_factor,
            chronic_factor=chronic_boost
        )
        
        # Store patient info for display
        pq._patient_info[entry_id] = {
            "name": p["name"],
            "age": p["age"],
            "symptoms": p["symptoms"],
            "chronic_conditions": p["chronic"],
            "department": p["dept"],
            "severity": triage_result["severity_level"],
            "explanation": triage_result["explanation"]
        }
        
        cm.update_department_status(p["dept"], random.randint(3, 12), random.randint(2, 5))
        
        # Log to activity logger
        logger = get_activity_logger()
        logger.log_patient_checkin(
            patient_name=p["name"],
            patient_id=100 + i,
            entry_id=entry_id,
            token=f"TKN-{entry_id}",
            department=p["dept"],
            symptoms=p["symptoms"],
            triage_score=triage_result["triage_score"],
            severity_level=triage_result["severity_level"],
            priority_score=round(priority, 3),
            wait_minutes=0
        )
        
        results.append({
            "name": p["name"],
            "severity": triage_result["severity_level"],
            "score": round(triage_result["triage_score"], 1),
            "score_10": triage_result["triage_score"],  # Already 1-10 scale
            "priority": round(priority, 3)
        })
    
    # Run AI auto-allocation after seeding
    allocator = get_ai_allocator()
    ai_results = allocator.auto_allocate_all_departments()
    ai_actions = [r for r in ai_results if r.get("executed")]
    
    return {
        "success": True,
        "message": f"Seeded {len(results)} demo patients",
        "patients": results,
        "stats": pq.get_stats(),
        "ai_actions_taken": len(ai_actions)
    }


@router.delete("/demo/clear")
async def clear_demo_data():
    """Clear all queue data for demo reset."""
    pq = get_priority_queue()
    cm = get_crowd_manager()
    
    # Clear queue
    pq._heap = []
    pq._entries = {}
    pq._removed = set()
    pq._patient_info = {}
    pq._current_patients = {}
    
    # Reset crowd manager
    cm._department_stats = {}
    cm._teleconsult_queue = []
    
    return {"success": True, "message": "Demo data cleared"}


# =============================================================================
# AI DOCTOR ALLOCATION
# =============================================================================

@router.get("/ai/insights")
async def ai_insights():
    """
    Get AI system insights and department analysis.
    
    Returns comprehensive AI analysis including:
    - Department utilization scores
    - Queue predictions
    - Staffing recommendations
    """
    allocator = get_ai_allocator()
    return allocator.get_ai_insights()


@router.post("/ai/analyze/{department}")
async def ai_analyze_department(department: str):
    """
    AI analysis for a specific department.
    
    Returns detailed metrics and allocation recommendation.
    """
    allocator = get_ai_allocator()
    
    metrics = allocator.analyze_department(department)
    decision = allocator.make_allocation_decision(department)
    score, factors = allocator.calculate_assignment_score(metrics)
    
    return {
        "department": department,
        "metrics": {
            "current_queue": metrics.current_queue,
            "capacity": metrics.capacity,
            "utilization": round(metrics.utilization, 1),
            "avg_wait_minutes": round(metrics.avg_wait_minutes, 1),
            "critical_patients": metrics.critical_patients,
            "spare_doctors_assigned": metrics.spare_doctors_assigned,
            "trend": metrics.trend,
            "predicted_queue_30min": metrics.predicted_queue_30min
        },
        "ai_analysis": {
            "score": round(score, 2),
            "factors": factors,
            "recommendation": {
                "action": decision.action,
                "confidence": round(decision.confidence, 2),
                "reason": decision.reason,
                "doctor_id": decision.doctor_id,
                "doctor_name": decision.doctor_name
            }
        }
    }


@router.post("/ai/auto-allocate")
async def ai_auto_allocate():
    """
    Run AI auto-allocation across all departments.
    
    Automatically assigns or releases spare doctors based on:
    - Current utilization
    - Queue trends
    - Critical patient counts
    - Wait times
    - Time of day patterns
    
    Returns list of actions taken.
    """
    allocator = get_ai_allocator()
    logger = get_activity_logger()
    
    results = allocator.auto_allocate_all_departments()
    
    actions_taken = [r for r in results if r.get("executed")]
    
    # Log each AI action
    for action in actions_taken:
        logger.log_ai_allocation(
            action=action.get("decision", {}).get("action", "unknown"),
            department=action.get("department", "unknown"),
            doctor_name=action.get("doctor_assigned", {}).get("name") or action.get("doctor_released", {}).get("name"),
            reason=action.get("decision", {}).get("reason", "AI decision"),
            confidence=action.get("decision", {}).get("confidence", 0),
            executed=True
        )
    
    return {
        "success": True,
        "departments_analyzed": len(results),
        "actions_taken": len(actions_taken),
        "results": results
    }


@router.post("/ai/auto-allocate/{department}")
async def ai_auto_allocate_department(department: str):
    """
    Run AI auto-allocation for a specific department.
    
    Analyzes department and executes allocation decision if confidence is high.
    """
    allocator = get_ai_allocator()
    pool = get_spare_doctor_pool()
    logger = get_activity_logger()
    
    decision = allocator.make_allocation_decision(department)
    
    result = {
        "department": department,
        "decision": {
            "action": decision.action,
            "confidence": round(decision.confidence, 2),
            "reason": decision.reason,
            "factors": decision.factors
        },
        "executed": False
    }
    
    # Execute if appropriate
    if decision.action == "assign" and decision.doctor_id:
        assignment = pool.assign_doctor(
            decision.doctor_id,
            department,
            f"AI Auto-Assignment: {decision.reason}",
            "ai_system"
        )
        if assignment and assignment.get("success"):
            result["executed"] = True
            result["doctor_assigned"] = {
                "id": decision.doctor_id,
                "name": decision.doctor_name
            }
            # Log AI action
            logger.log_ai_allocation(
                action="assign",
                department=department,
                doctor_name=decision.doctor_name,
                reason=decision.reason,
                confidence=decision.confidence,
                executed=True
            )
            
    elif decision.action == "release" and decision.doctor_id:
        release = pool.release_doctor(
            decision.doctor_id,
            f"AI Auto-Release: {decision.reason}",
            "ai_system"
        )
        if release and release.get("success"):
            result["executed"] = True
            result["doctor_released"] = {
                "id": decision.doctor_id,
                "name": decision.doctor_name
            }
            # Log AI action
            logger.log_ai_allocation(
                action="release",
                department=department,
                doctor_name=decision.doctor_name,
                reason=decision.reason,
                confidence=decision.confidence,
                executed=True
            )
    
    return result


# =============================================================================
# ACTIVITY LOGS
# =============================================================================

@router.get("/activity/logs")
async def get_activity_logs(
    limit: int = 100,
    activity_type: Optional[str] = None,
    department: Optional[str] = None
):
    """
    Get activity logs with optional filtering.
    
    Shows:
    - Patient check-ins with severity scores (1-10 scale)
    - Spare doctor assignments/releases
    - AI allocation decisions
    - Emergency overrides
    """
    logger = get_activity_logger()
    logs = logger.get_logs(limit=limit, activity_type=activity_type, department=department)
    stats = logger.get_stats()
    
    return {
        "success": True,
        "logs": logs,
        "stats": stats,
        "total": len(logs)
    }


@router.get("/activity/stats")
async def get_activity_stats():
    """Get activity statistics."""
    logger = get_activity_logger()
    return {
        "success": True,
        "stats": logger.get_stats()
    }


# =============================================================================
# WAIT TIME PROTECTION
# =============================================================================

@router.get("/ai/wait-impact/{department}")
async def get_wait_time_impact(department: str):
    """
    Calculate wait time impact when critical patients are in queue.
    
    Shows how critical patients affect wait times for regular patients
    and recommends spare doctor assignments to protect wait times.
    """
    allocator = get_ai_allocator()
    impact = allocator.calculate_wait_time_impact(department)
    return impact


@router.post("/ai/protect-wait-times/{department}")
async def protect_wait_times(department: str):
    """
    Automatically assign spare doctors to protect wait times.
    
    When critical patients arrive and would increase wait times for
    existing patients, this endpoint assigns spare doctors to handle
    the surge and maintain original wait time commitments.
    """
    allocator = get_ai_allocator()
    result = allocator.protect_wait_times(department)
    return result


@router.post("/ai/protect-all")
async def protect_all_wait_times():
    """
    Run wait time protection for ALL departments.
    
    Automatically checks each department and assigns spare doctors
    where needed to prevent wait time increases from critical patients.
    """
    allocator = get_ai_allocator()
    result = allocator.auto_protect_all_departments()
    return result
