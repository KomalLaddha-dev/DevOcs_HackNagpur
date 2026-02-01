"""
Priority Queue Algorithm for Patient Scheduling

Implements a dynamic priority queue that considers:
- Triage severity score
- Wait time
- Patient age
- Chronic conditions
"""

import heapq
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any


@dataclass(order=True)
class PriorityPatient:
    """Patient entry with priority ordering."""
    priority: float
    patient_id: int = field(compare=False)
    triage_score: int = field(compare=False)
    check_in_time: datetime = field(compare=False)
    age: int = field(compare=False)
    has_chronic_condition: bool = field(compare=False)
    
    def __post_init__(self):
        # Negate priority for max-heap behavior
        self.priority = -self.priority


class SmartPriorityQueue:
    """
    Smart Priority Queue implementation.
    
    Priority Calculation:
    P = w₁×S + w₂×W + w₃×A + w₄×C
    
    Where:
    - S: Normalized triage severity (0-1)
    - W: Normalized wait time (0-1)  
    - A: Age factor (1.0 or 1.2 for elderly/children)
    - C: Chronic condition factor (1.0 or 1.2)
    """
    
    # Configurable weights
    SEVERITY_WEIGHT = 0.40
    WAIT_TIME_WEIGHT = 0.30
    AGE_WEIGHT = 0.15
    CHRONIC_WEIGHT = 0.15
    
    # Thresholds
    MAX_WAIT_MINUTES = 180  # Cap wait time normalization at 3 hours
    ELDERLY_AGE = 65
    CHILD_AGE = 5
    
    def __init__(self):
        self._heap: List[PriorityPatient] = []
        self._entry_finder: dict = {}
        self._counter = 0
    
    def add_patient(
        self,
        patient_id: int,
        triage_score: int,
        age: int,
        has_chronic_condition: bool = False
    ) -> float:
        """
        Add a patient to the queue.
        
        Returns the calculated priority score.
        """
        check_in_time = datetime.now()
        priority = self.calculate_priority(
            triage_score=triage_score,
            wait_time_minutes=0,
            age=age,
            has_chronic_condition=has_chronic_condition
        )
        
        entry = PriorityPatient(
            priority=priority,
            patient_id=patient_id,
            triage_score=triage_score,
            check_in_time=check_in_time,
            age=age,
            has_chronic_condition=has_chronic_condition
        )
        
        heapq.heappush(self._heap, entry)
        self._entry_finder[patient_id] = entry
        self._counter += 1
        
        return priority
    
    def get_next_patient(self) -> Optional[PriorityPatient]:
        """Remove and return the highest priority patient."""
        while self._heap:
            patient = heapq.heappop(self._heap)
            if patient.patient_id in self._entry_finder:
                del self._entry_finder[patient.patient_id]
                return patient
        return None
    
    def peek(self) -> Optional[PriorityPatient]:
        """View the highest priority patient without removing."""
        while self._heap:
            if self._heap[0].patient_id in self._entry_finder:
                return self._heap[0]
            heapq.heappop(self._heap)
        return None
    
    def get_position(self, patient_id: int) -> int:
        """Get patient's position in queue (1-indexed)."""
        # Create sorted list to find position
        sorted_patients = sorted(
            [p for p in self._entry_finder.values()],
            key=lambda x: x.priority
        )
        
        for i, patient in enumerate(sorted_patients):
            if patient.patient_id == patient_id:
                return i + 1
        return -1
    
    def update_priorities(self):
        """
        Update all patient priorities based on current wait times.
        Should be called periodically (e.g., every 5 minutes).
        """
        now = datetime.now()
        new_heap = []
        
        for patient in self._entry_finder.values():
            wait_minutes = (now - patient.check_in_time).seconds // 60
            new_priority = self.calculate_priority(
                triage_score=patient.triage_score,
                wait_time_minutes=wait_minutes,
                age=patient.age,
                has_chronic_condition=patient.has_chronic_condition
            )
            
            updated = PriorityPatient(
                priority=new_priority,
                patient_id=patient.patient_id,
                triage_score=patient.triage_score,
                check_in_time=patient.check_in_time,
                age=patient.age,
                has_chronic_condition=patient.has_chronic_condition
            )
            
            heapq.heappush(new_heap, updated)
            self._entry_finder[patient.patient_id] = updated
        
        self._heap = new_heap
    
    def calculate_priority(
        self,
        triage_score: int,
        wait_time_minutes: int,
        age: int,
        has_chronic_condition: bool
    ) -> float:
        """
        Calculate priority score for a patient.
        
        Returns a score between 0-100 (higher = more urgent).
        """
        # Normalize triage score (1-5 → 0-1)
        normalized_severity = (triage_score - 1) / 4.0
        
        # Normalize wait time (capped at MAX_WAIT_MINUTES)
        normalized_wait = min(wait_time_minutes / self.MAX_WAIT_MINUTES, 1.0)
        
        # Age factor (boost for elderly and children)
        age_factor = 1.2 if (age >= self.ELDERLY_AGE or age <= self.CHILD_AGE) else 1.0
        
        # Chronic condition factor
        chronic_factor = 1.2 if has_chronic_condition else 1.0
        
        # Calculate weighted sum
        priority = (
            self.SEVERITY_WEIGHT * normalized_severity * 100 +
            self.WAIT_TIME_WEIGHT * normalized_wait * 100 +
            self.AGE_WEIGHT * (age_factor - 1) * 100 +
            self.CHRONIC_WEIGHT * (chronic_factor - 1) * 100
        )
        
        return round(priority, 2)
    
    def emergency_override(self, patient_id: int) -> bool:
        """Move a patient to maximum priority (emergency)."""
        if patient_id in self._entry_finder:
            patient = self._entry_finder[patient_id]
            
            # Create new entry with maximum priority
            emergency_patient = PriorityPatient(
                priority=999.0,
                patient_id=patient.patient_id,
                triage_score=5,
                check_in_time=patient.check_in_time,
                age=patient.age,
                has_chronic_condition=patient.has_chronic_condition
            )
            
            heapq.heappush(self._heap, emergency_patient)
            self._entry_finder[patient_id] = emergency_patient
            return True
        return False
    
    def __len__(self) -> int:
        return len(self._entry_finder)
    
    def get_queue_snapshot(self) -> List[dict]:
        """Get current queue as sorted list."""
        sorted_patients = sorted(
            self._entry_finder.values(),
            key=lambda x: x.priority
        )
        
        return [
            {
                "position": i + 1,
                "patient_id": p.patient_id,
                "priority": abs(p.priority),
                "triage_score": p.triage_score,
                "wait_time": (datetime.now() - p.check_in_time).seconds // 60
            }
            for i, p in enumerate(sorted_patients)
        ]
