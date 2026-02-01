"""
SmartCare Triage Engine
========================
Rule-based, explainable triage scoring system.
NO black-box AI - every decision can be explained to judges.

Algorithm:
1. Match symptoms against severity keyword database
2. Apply age risk factor
3. Add chronic condition boosts  
4. Consider symptom duration
5. Calculate final weighted score
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from app.core.constants import (
    CRITICAL_SYMPTOMS, URGENT_SYMPTOMS, MODERATE_SYMPTOMS, 
    LOW_SYMPTOMS, ROUTINE_SYMPTOMS, AGE_RISK_FACTORS,
    CHRONIC_CONDITIONS, SEVERITY_DESCRIPTIONS, BASE_WAIT_TIMES,
    TELECONSULT_ELIGIBLE
)


class TriageEngine:
    """
    Explainable rule-based triage engine.
    
    Scoring Formula:
    ================
    Final Score = base_symptom_score 
                  × age_factor 
                  + chronic_boost
                  + duration_adjustment
                  + emergency_flag_boost
    
    Output: Score 1-5 where 5 = most critical
    """
    
    @staticmethod
    def calculate_age(date_of_birth: date) -> int:
        """Calculate age from date of birth."""
        today = date.today()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
    
    @staticmethod
    def get_age_risk_factor(age: int) -> float:
        """
        Get risk multiplier based on age.
        
        Logic:
        - Infants (0-2): 1.5x risk - vulnerable, can't communicate
        - Elderly (70+): 1.4-1.5x risk - higher complication rates
        - Adults (18-60): 1.0x baseline risk
        """
        for (min_age, max_age), factor in AGE_RISK_FACTORS.items():
            if min_age <= age <= max_age:
                return factor
        return 1.0
    
    @staticmethod
    def calculate_symptom_score(symptoms: List[str], description: str = "") -> tuple[int, List[str]]:
        """
        Match symptoms against severity database.
        
        Returns:
            tuple: (severity_score 1-10, list of matched keywords for explanation)
        """
        text = " ".join(symptoms).lower() + " " + description.lower()
        matched_keywords = []
        
        # Check critical symptoms first (highest priority) -> 9-10
        for symptom, score in CRITICAL_SYMPTOMS.items():
            if symptom in text:
                matched_keywords.append(f"CRITICAL: {symptom}")
                return (10, matched_keywords)  # Immediate return for critical
        
        # Check urgent symptoms -> 7-8
        for symptom, score in URGENT_SYMPTOMS.items():
            if symptom in text:
                matched_keywords.append(f"URGENT: {symptom}")
                return (8, matched_keywords)
        
        # Check moderate symptoms -> 5-6
        max_score = 2
        for symptom, score in MODERATE_SYMPTOMS.items():
            if symptom in text:
                matched_keywords.append(f"MODERATE: {symptom}")
                max_score = max(max_score, 6)
        
        if max_score == 6:
            return (6, matched_keywords)
        
        # Check low severity symptoms -> 3-4
        for symptom, score in LOW_SYMPTOMS.items():
            if symptom in text:
                matched_keywords.append(f"LOW: {symptom}")
                max_score = max(max_score, 4)
        
        if max_score == 4:
            return (4, matched_keywords)
        
        # Check routine symptoms -> 1-2
        for symptom, score in ROUTINE_SYMPTOMS.items():
            if symptom in text:
                matched_keywords.append(f"ROUTINE: {symptom}")
                return (2, matched_keywords)
        
        # Default: low if no match (safety first)
        return (3, ["No specific symptom matched - defaulting to LOW priority"])
    
    @staticmethod
    def calculate_chronic_boost(conditions: List[str]) -> tuple[float, List[str]]:
        """
        Calculate priority boost from chronic conditions.
        
        Returns:
            tuple: (boost_value, list of matched conditions)
        """
        boost = 0.0
        matched = []
        
        conditions_text = " ".join(conditions).lower()
        
        for condition, boost_value in CHRONIC_CONDITIONS.items():
            if condition in conditions_text:
                boost += boost_value
                matched.append(f"{condition}: +{boost_value}")
        
        # Cap total boost at 1.0
        return (min(boost, 1.0), matched)
    
    @staticmethod
    def get_duration_adjustment(duration_hours: int) -> tuple[float, str]:
        """
        Adjust severity based on symptom duration.
        
        Logic:
        - < 2 hours: neutral (just started)
        - 2-24 hours: +0.2 (persisting)
        - 24-72 hours: +0.5 (needs attention)
        - > 72 hours: +0.8 (delayed care)
        """
        if duration_hours < 2:
            return (0.0, "Recent onset")
        elif duration_hours < 24:
            return (0.2, "Symptoms persisting for hours")
        elif duration_hours < 72:
            return (0.5, "Symptoms ongoing for 1-3 days")
        else:
            return (0.8, "Symptoms present for over 3 days")
    
    @classmethod
    def perform_triage(
        cls,
        symptoms: List[str],
        description: str,
        age: int,
        chronic_conditions: List[str] = None,
        duration_hours: int = 0,
        is_emergency: bool = False,
        self_severity: int = 5  # 1-10 scale from patient
    ) -> Dict:
        """
        Main triage function - calculates final priority score.
        
        Returns a complete, explainable triage result.
        """
        chronic_conditions = chronic_conditions or []
        explanation_parts = []
        
        # Step 1: Calculate base symptom score
        base_score, symptom_matches = cls.calculate_symptom_score(symptoms, description)
        explanation_parts.append(f"Base symptom score: {base_score}/5")
        explanation_parts.extend(symptom_matches)
        
        # Step 2: Apply age factor
        age_factor = cls.get_age_risk_factor(age)
        explanation_parts.append(f"Age ({age} years) risk factor: {age_factor}x")
        
        # Step 3: Calculate chronic condition boost
        chronic_boost, chronic_matches = cls.calculate_chronic_boost(chronic_conditions)
        if chronic_matches:
            explanation_parts.append(f"Chronic condition boost: +{chronic_boost}")
            explanation_parts.extend(chronic_matches)
        
        # Step 4: Duration adjustment
        duration_adj, duration_reason = cls.get_duration_adjustment(duration_hours)
        if duration_adj > 0:
            explanation_parts.append(f"Duration adjustment: +{duration_adj} ({duration_reason})")
        
        # Step 5: Emergency override
        emergency_boost = 2.0 if is_emergency else 0.0
        if is_emergency:
            explanation_parts.append("🚨 EMERGENCY FLAG: +2.0 (Manual override)")
        
        # Step 6: Self-assessment consideration (weighted low - patients often overestimate)
        self_factor = (self_severity / 10) * 0.5  # Max 0.5 boost for 1-10 scale
        explanation_parts.append(f"Self-reported severity ({self_severity}/10): +{self_factor:.2f}")
        
        # Calculate final score on 1-10 scale
        raw_score = (
            base_score  # Already 1-10 from symptom matching
            + (age_factor - 1.0) * 2  # Age adjustment (-1 to +1 range scaled)
            + chronic_boost * 2  # Chronic boost scaled for 1-10
            + duration_adj  # Duration adjustment
            + emergency_boost  # Emergency boost
            + self_factor  # Self assessment
        )
        
        # Clamp to 1-10 range
        final_score = max(1, min(10, round(raw_score)))
        
        # Get severity description (1-10 scale)
        severity_info = SEVERITY_DESCRIPTIONS[final_score]
        
        # Determine if eligible for teleconsult
        teleconsult_eligible = (
            final_score <= TELECONSULT_ELIGIBLE["max_severity_score"]
            and not is_emergency
        )
        
        # Calculate estimated wait time (1-10 scale)
        base_wait = BASE_WAIT_TIMES[final_score]
        
        return {
            "triage_score": final_score,  # Now 1-10 scale
            "severity_level": severity_info["level"],
            "severity_color": severity_info["color"],
            "recommended_action": severity_info["action"],
            "estimated_wait_minutes": base_wait,
            "teleconsult_eligible": teleconsult_eligible,
            "explanation": explanation_parts,
            "raw_score": round(raw_score, 2),
            "calculation_breakdown": {
                "base_symptom_score": base_score,
                "age_factor": age_factor,
                "chronic_boost": chronic_boost,
                "duration_adjustment": duration_adj,
                "emergency_boost": emergency_boost,
                "self_assessment_factor": round(self_factor, 2)
            }
        }


# Convenience function for API use
def triage_patient(
    symptoms: List[str],
    description: str = "",
    age: int = 30,
    chronic_conditions: List[str] = None,
    duration_hours: int = 0,
    is_emergency: bool = False,
    self_severity: int = 5
) -> Dict:
    """Convenience function to perform triage."""
    return TriageEngine.perform_triage(
        symptoms=symptoms,
        description=description,
        age=age,
        chronic_conditions=chronic_conditions,
        duration_hours=duration_hours,
        is_emergency=is_emergency,
        self_severity=self_severity
    )
