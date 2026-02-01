"""
SmartCare AI Triage Model
NLP-based symptom analysis and severity scoring.
"""

import re
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class TriageResult:
    """Result from triage analysis."""
    severity_score: int  # 1-5
    confidence: float
    matched_symptoms: List[str]
    recommended_action: str
    explanation: str


class SymptomAnalyzer:
    """
    NLP-based symptom analyzer for medical triage.
    
    Uses keyword matching, severity scoring, and rule-based
    classification to determine patient urgency level.
    """
    
    def __init__(self):
        self._load_medical_knowledge()
    
    def _load_medical_knowledge(self):
        """Load medical knowledge base for symptom analysis."""
        # Symptom severity mappings
        self.symptom_severity = {
            # Critical (5)
            "chest pain": 5, "difficulty breathing": 5, "unconscious": 5,
            "severe bleeding": 5, "stroke symptoms": 5, "heart attack": 5,
            "seizure": 5, "anaphylaxis": 5, "choking": 5,
            
            # Urgent (4)
            "high fever": 4, "severe pain": 4, "vomiting blood": 4,
            "confusion": 4, "severe headache": 4, "broken bone": 4,
            "deep cut": 4, "burns": 4, "abdominal pain": 4,
            
            # Moderate (3)
            "fever": 3, "persistent cough": 3, "infection": 3,
            "moderate pain": 3, "ear pain": 3, "urinary issues": 3,
            "rash": 3, "sprain": 3, "minor fracture": 3,
            
            # Low (2)
            "cold": 2, "mild headache": 2, "sore throat": 2,
            "runny nose": 2, "minor pain": 2, "fatigue": 2,
            "muscle ache": 2, "mild nausea": 2,
            
            # Minimal (1)
            "prescription refill": 1, "follow-up": 1, "checkup": 1,
            "vaccination": 1, "routine consultation": 1
        }
        
        # Symptom patterns (regex)
        self.symptom_patterns = {
            "chest pain": r"chest\s*(pain|tight|pressure|discomfort)",
            "difficulty breathing": r"(breath|breathing|breathe).*(difficult|hard|trouble|short)",
            "high fever": r"(high|severe)\s*fever|fever.*(high|39|40|104|105)",
            "severe pain": r"(severe|intense|extreme|unbearable)\s*pain",
            "vomiting blood": r"(vomit|throw up).*(blood|red)",
        }
        
        # Body system keywords for specialty routing
        self.body_systems = {
            "cardiovascular": ["heart", "chest", "blood pressure", "pulse"],
            "respiratory": ["breathing", "lung", "cough", "asthma"],
            "neurological": ["headache", "dizzy", "numbness", "seizure"],
            "gastrointestinal": ["stomach", "nausea", "vomiting", "diarrhea"],
            "musculoskeletal": ["bone", "joint", "muscle", "back pain"],
            "dermatological": ["skin", "rash", "itching", "wound"]
        }
    
    def analyze(self, symptoms: List[str], description: str = "") -> TriageResult:
        """
        Analyze symptoms and return triage assessment.
        
        Args:
            symptoms: List of symptom keywords
            description: Free-text symptom description
            
        Returns:
            TriageResult with severity score and recommendations
        """
        combined_text = " ".join(symptoms).lower() + " " + description.lower()
        
        # Find matching symptoms
        matched = self._match_symptoms(combined_text)
        
        # Calculate severity score
        severity = self._calculate_severity(matched)
        
        # Calculate confidence
        confidence = self._calculate_confidence(matched, combined_text)
        
        # Get recommendation
        recommendation = self._get_recommendation(severity)
        
        # Generate explanation
        explanation = self._generate_explanation(severity, matched)
        
        return TriageResult(
            severity_score=severity,
            confidence=confidence,
            matched_symptoms=matched,
            recommended_action=recommendation,
            explanation=explanation
        )
    
    def _match_symptoms(self, text: str) -> List[str]:
        """Match symptoms from text using keywords and patterns."""
        matched = []
        
        # Direct keyword matching
        for symptom in self.symptom_severity.keys():
            if symptom in text:
                matched.append(symptom)
        
        # Pattern matching for complex symptoms
        for symptom, pattern in self.symptom_patterns.items():
            if re.search(pattern, text) and symptom not in matched:
                matched.append(symptom)
        
        return matched
    
    def _calculate_severity(self, matched_symptoms: List[str]) -> int:
        """Calculate overall severity from matched symptoms."""
        if not matched_symptoms:
            return 2  # Default to low severity
        
        # Get max severity from matched symptoms
        severities = [
            self.symptom_severity.get(s, 2) 
            for s in matched_symptoms
        ]
        
        # Use max severity (critical symptoms override)
        return max(severities)
    
    def _calculate_confidence(self, matched: List[str], text: str) -> float:
        """Calculate confidence score for the assessment."""
        if not matched:
            return 0.3  # Low confidence if no matches
        
        # Base confidence from matches
        base_confidence = min(len(matched) * 0.2, 0.8)
        
        # Boost for exact matches
        exact_boost = sum(0.05 for m in matched if m in text)
        
        return min(base_confidence + exact_boost, 0.95)
    
    def _get_recommendation(self, severity: int) -> str:
        """Get recommended action based on severity."""
        recommendations = {
            5: "EMERGENCY: Proceed to Emergency Room immediately",
            4: "URGENT: Priority queue - See doctor within 15 minutes",
            3: "MODERATE: Standard queue - Estimated wait 30-60 minutes",
            2: "LOW: Extended queue or teleconsultation recommended",
            1: "MINIMAL: Teleconsultation sufficient - No in-person visit needed"
        }
        return recommendations.get(severity, "Please consult healthcare provider")
    
    def _generate_explanation(self, severity: int, matched: List[str]) -> str:
        """Generate human-readable explanation."""
        if not matched:
            return "No specific symptoms identified. Default assessment applied."
        
        symptom_list = ", ".join(matched[:3])
        severity_names = {5: "critical", 4: "urgent", 3: "moderate", 2: "low", 1: "minimal"}
        
        return f"Based on symptoms ({symptom_list}), assessed as {severity_names[severity]} severity."
    
    def get_specialty_recommendation(self, symptoms: List[str]) -> str:
        """Recommend medical specialty based on symptoms."""
        combined = " ".join(symptoms).lower()
        
        scores = {}
        for specialty, keywords in self.body_systems.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > 0:
                scores[specialty] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "general"


# Singleton instance
symptom_analyzer = SymptomAnalyzer()
