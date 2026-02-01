"""
SmartCare Constants & Configuration
=====================================
All system-wide constants for triage, queue management, and scheduling.
These are the "rules" that make the system explainable to judges.
"""

# =============================================================================
# TRIAGE SCORING RULES (Explainable AI)
# =============================================================================

# Symptom severity mappings (keyword -> base score)
CRITICAL_SYMPTOMS = {
    "chest pain": 5, "difficulty breathing": 5, "severe bleeding": 5,
    "unconscious": 5, "stroke": 5, "heart attack": 5, "seizure": 5,
    "anaphylaxis": 5, "severe allergic": 5, "cannot breathe": 5,
    "cardiac arrest": 5, "major trauma": 5, "not breathing": 5,
    "choking": 5, "overdose": 5, "severe trauma": 5
}

URGENT_SYMPTOMS = {
    "high fever": 4, "severe pain": 4, "vomiting blood": 4,
    "confusion": 4, "severe headache": 4, "abdominal pain": 4,
    "broken bone": 4, "fracture": 4, "deep cut": 4, "burns": 4,
    "blood in urine": 4, "fainting": 4, "severe vomiting": 4,
    "stomach pain": 4, "abdomen pain": 4, "intense pain": 4,
    "heavy bleeding": 4, "accident": 4, "injury": 4,
    "breathing problem": 4, "shortness of breath": 4
}

MODERATE_SYMPTOMS = {
    "fever": 3, "persistent cough": 3, "moderate pain": 3,
    "infection": 3, "rash": 3, "ear pain": 3, "sore throat": 3,
    "sprain": 3, "minor burns": 3, "dizziness": 3, "nausea": 3,
    "cough": 3, "headache": 3, "body ache": 3, "joint pain": 3,
    "vomiting": 3, "diarrhea": 3, "back pain": 3, "neck pain": 3,
    "swelling": 3, "weakness": 3, "pain": 3
}

LOW_SYMPTOMS = {
    "cold": 2, "mild headache": 2, "runny nose": 2,
    "minor pain": 2, "mild cough": 2, "fatigue": 2,
    "minor injury": 2, "skin irritation": 2, "allergies": 2,
    "sneezing": 2, "congestion": 2, "mild fever": 2, "tired": 2
}

ROUTINE_SYMPTOMS = {
    "prescription refill": 1, "follow-up": 1, "checkup": 1,
    "vaccination": 1, "health certificate": 1, "routine exam": 1,
    "consultation": 1, "general checkup": 1
}

# =============================================================================
# AGE RISK FACTORS
# =============================================================================
AGE_RISK_FACTORS = {
    (0, 2): 1.5,      # Infants - highest risk
    (3, 5): 1.3,      # Toddlers
    (6, 12): 1.1,     # Children
    (13, 17): 1.0,    # Teens
    (18, 40): 1.0,    # Adults
    (41, 60): 1.1,    # Middle-aged
    (61, 70): 1.3,    # Seniors
    (71, 80): 1.4,    # Elderly
    (81, 120): 1.5,   # Very elderly
}

# =============================================================================
# CHRONIC CONDITIONS (boost priority)
# =============================================================================
CHRONIC_CONDITIONS = {
    "diabetes": 0.2,
    "heart disease": 0.3,
    "hypertension": 0.15,
    "asthma": 0.2,
    "copd": 0.25,
    "cancer": 0.3,
    "kidney disease": 0.25,
    "liver disease": 0.2,
    "immunocompromised": 0.3,
    "pregnancy": 0.2,
}

# =============================================================================
# PRIORITY CALCULATION WEIGHTS
# =============================================================================
PRIORITY_WEIGHTS = {
    "severity": 0.40,      # Symptom severity is most important
    "wait_time": 0.25,     # Fairness: waiting longer = higher priority
    "age_factor": 0.15,    # Age vulnerability
    "chronic_factor": 0.10,  # Chronic conditions
    "emergency_flag": 0.10,  # Manual emergency override
}

# =============================================================================
# QUEUE THRESHOLDS
# =============================================================================
QUEUE_THRESHOLDS = {
    "max_queue_length": 50,        # Trigger crowd management
    "critical_queue_length": 75,   # Trigger spare doctor allocation
    "max_wait_time_minutes": 120,  # 2 hours max wait
    "critical_wait_time_minutes": 180,  # 3 hours = escalate
}

# =============================================================================
# TELE-CONSULTATION RULES
# =============================================================================
TELECONSULT_ELIGIBLE = {
    "max_severity_score": 4,  # Only severity 1-4 eligible (1-10 scale)
    "symptoms": [
        "cold", "mild cough", "follow-up", "prescription refill",
        "routine checkup", "minor skin issue", "dietary consultation",
        "mental health follow-up", "medication query"
    ]
}

# =============================================================================
# ESTIMATED WAIT TIMES (minutes per severity level) - 1-10 scale
# =============================================================================
BASE_WAIT_TIMES = {
    10: 0,    # Critical - immediate
    9: 5,     # Critical - immediate
    8: 10,    # Urgent - ~10 min
    7: 20,    # Urgent - ~20 min
    6: 35,    # Moderate-High - ~35 min
    5: 50,    # Moderate - ~50 min
    4: 70,    # Moderate-Low - ~70 min
    3: 90,    # Low - ~1.5 hours
    2: 110,   # Minimal - ~2 hours
    1: 120,   # Minimal - ~2 hours or teleconsult
}

# =============================================================================
# SPARE DOCTOR POOL CONFIG
# =============================================================================
SPARE_DOCTOR_CONFIG = {
    "activation_threshold": 0.8,    # 80% capacity triggers spare doctors
    "max_spare_doctors_per_dept": 3,
    "teleconsult_priority_max": 2,  # Spare doctors handle low priority only
}

# =============================================================================
# SEVERITY LEVEL DESCRIPTIONS - 1-10 scale
# =============================================================================
SEVERITY_DESCRIPTIONS = {
    10: {"level": "CRITICAL", "color": "red", "action": "Immediate attention required"},
    9: {"level": "CRITICAL", "color": "red", "action": "Immediate attention required"},
    8: {"level": "URGENT", "color": "orange", "action": "Needs prompt medical attention"},
    7: {"level": "URGENT", "color": "orange", "action": "Needs attention within 30 minutes"},
    6: {"level": "MODERATE", "color": "yellow", "action": "Should be seen within 1 hour"},
    5: {"level": "MODERATE", "color": "yellow", "action": "Should be seen within 1-2 hours"},
    4: {"level": "LOW", "color": "green", "action": "Can wait up to 2 hours"},
    3: {"level": "LOW", "color": "green", "action": "Can wait up to 4 hours"},
    2: {"level": "MINIMAL", "color": "blue", "action": "Teleconsultation recommended"},
    1: {"level": "MINIMAL", "color": "blue", "action": "Teleconsultation or scheduled visit"},
}

# Legacy 1-5 to 1-10 mapping for backward compatibility
SEVERITY_5_TO_10 = {
    5: 10,  # CRITICAL
    4: 8,   # URGENT
    3: 6,   # MODERATE
    2: 3,   # LOW
    1: 1,   # MINIMAL
}

# =============================================================================
# DEPARTMENT MAPPINGS
# =============================================================================
DEPARTMENTS = {
    "GENERAL": {"code": "GEN", "base_capacity": 30},
    "EMERGENCY": {"code": "EMR", "base_capacity": 20},
    "PEDIATRICS": {"code": "PED", "base_capacity": 25},
    "CARDIOLOGY": {"code": "CAR", "base_capacity": 15},
    "ORTHOPEDICS": {"code": "ORT", "base_capacity": 20},
    "NEUROLOGY": {"code": "NEU", "base_capacity": 15},
    "DERMATOLOGY": {"code": "DRM", "base_capacity": 25},
    "GYNECOLOGY": {"code": "GYN", "base_capacity": 20},
}
