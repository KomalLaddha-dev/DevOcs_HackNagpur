"""
AI Triage Service - Symptom Analysis and Severity Scoring
"""

from typing import List
import re

from app.schemas.patient import SymptomSubmission, TriageResult


class TriageService:
    """
    AI-powered triage service for symptom analysis.
    Uses NLP and rule-based scoring for severity assessment.
    """
    
    # Critical symptoms that indicate high severity
    CRITICAL_SYMPTOMS = [
        "chest pain", "difficulty breathing", "severe bleeding",
        "unconscious", "stroke", "heart attack", "seizure",
        "severe allergic reaction", "anaphylaxis"
    ]
    
    # Urgent symptoms
    URGENT_SYMPTOMS = [
        "high fever", "severe pain", "vomiting blood",
        "confusion", "severe headache", "abdominal pain",
        "broken bone", "deep cut", "burns"
    ]
    
    # Moderate symptoms
    MODERATE_SYMPTOMS = [
        "fever", "persistent cough", "minor injury",
        "infection", "rash", "ear pain", "sore throat"
    ]
    
    # Low severity symptoms
    LOW_SYMPTOMS = [
        "cold", "mild headache", "runny nose",
        "minor pain", "prescription refill", "follow-up"
    ]
    
    SEVERITY_DESCRIPTIONS = {
        5: "Critical - Immediate attention required",
        4: "Urgent - Needs prompt medical attention",
        3: "Moderate - Should be seen within 1-2 hours",
        2: "Low Priority - Can wait up to 4 hours",
        1: "Minimal - Routine care / Teleconsultation recommended"
    }
    
    async def analyze_symptoms(self, submission: SymptomSubmission) -> TriageResult:
        """
        Analyze submitted symptoms and return triage assessment.
        
        Algorithm:
        1. Extract keywords from symptoms
        2. Match against severity categories
        3. Consider duration and self-assessment
        4. Calculate final triage score
        """
        symptoms_text = " ".join(submission.symptoms).lower() + " " + submission.description.lower()
        
        # Calculate base score from symptoms
        base_score = self._calculate_symptom_score(symptoms_text)
        
        # Adjust based on duration
        duration_factor = self._get_duration_factor(submission.duration)
        
        # Consider self-assessment (with limits)
        self_factor = min(submission.severity_self_assessment / 10, 1.0)
        
        # Calculate final score (weighted average)
        final_score = round(
            base_score * 0.6 +
            duration_factor * 0.2 +
            self_factor * 5 * 0.2
        )
        
        # Clamp to valid range
        final_score = max(1, min(5, final_score))
        
        # Determine recommended action
        action = self._get_recommended_action(final_score)
        
        # Estimate wait time
        wait_time = self._estimate_wait_time(final_score)
        
        # Generate explanation
        explanation = self._generate_explanation(final_score, symptoms_text)
        
        return TriageResult(
            triage_score=final_score,
            severity_level=self.SEVERITY_DESCRIPTIONS[final_score],
            recommended_action=action,
            estimated_wait_time=wait_time,
            priority_score=final_score * 20,
            explanation=explanation
        )
    
    def _calculate_symptom_score(self, symptoms_text: str) -> int:
        """Calculate severity score based on symptom keywords."""
        # Check for critical symptoms
        for symptom in self.CRITICAL_SYMPTOMS:
            if symptom in symptoms_text:
                return 5
        
        # Check for urgent symptoms
        for symptom in self.URGENT_SYMPTOMS:
            if symptom in symptoms_text:
                return 4
        
        # Check for moderate symptoms
        for symptom in self.MODERATE_SYMPTOMS:
            if symptom in symptoms_text:
                return 3
        
        # Check for low symptoms
        for symptom in self.LOW_SYMPTOMS:
            if symptom in symptoms_text:
                return 2
        
        # Default to moderate if no matches
        return 2
    
    def _get_duration_factor(self, duration: str) -> float:
        """Get severity factor based on symptom duration."""
        duration_lower = duration.lower()
        
        if any(word in duration_lower for word in ["sudden", "minutes", "just now"]):
            return 1.0  # Sudden onset can be serious
        elif any(word in duration_lower for word in ["hours", "today"]):
            return 0.8
        elif any(word in duration_lower for word in ["days", "few days"]):
            return 0.6
        elif any(word in duration_lower for word in ["week", "weeks"]):
            return 0.4
        else:
            return 0.5
    
    def _get_recommended_action(self, score: int) -> str:
        """Get recommended action based on triage score."""
        actions = {
            5: "Proceed to Emergency Room immediately",
            4: "Priority queue - Will be seen shortly",
            3: "Standard queue - In-person consultation",
            2: "Extended queue - Consider teleconsultation",
            1: "Teleconsultation recommended - No in-person visit needed"
        }
        return actions.get(score, "Please consult a healthcare provider")
    
    def _estimate_wait_time(self, score: int) -> int:
        """Estimate wait time in minutes based on triage score."""
        wait_times = {
            5: 0,   # Immediate
            4: 15,  # 15 minutes
            3: 45,  # 45 minutes
            2: 90,  # 1.5 hours
            1: 120  # 2 hours (or teleconsult)
        }
        return wait_times.get(score, 60)
    
    def _generate_explanation(self, score: int, symptoms: str) -> str:
        """Generate human-readable explanation of triage decision."""
        explanations = {
            5: f"Critical symptoms detected. Immediate medical attention is required.",
            4: f"Urgent symptoms identified. You will be prioritized in the queue.",
            3: f"Moderate symptoms noted. You will be seen in the standard queue.",
            2: f"Low severity symptoms. Consider a teleconsultation to save time.",
            1: f"Minimal severity. A teleconsultation can effectively address your concerns."
        }
        return explanations.get(score, "Please proceed to registration.")
