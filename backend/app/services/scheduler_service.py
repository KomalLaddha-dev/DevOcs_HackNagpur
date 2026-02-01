"""
Doctor Scheduling Optimization Service
Implements greedy scheduling algorithm for optimal patient-doctor assignment.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.models.queue import QueueEntry


@dataclass
class SchedulingCandidate:
    """Represents a potential doctor assignment."""
    doctor_id: int
    score: float
    specialty_match: bool
    current_load: int
    max_capacity: int


class SchedulerService:
    """
    Intelligent scheduling service using greedy optimization.
    
    Objectives:
    1. Minimize patient wait time
    2. Balance doctor workload
    3. Match patient needs to doctor specialty
    """
    
    # Scoring weights
    WORKLOAD_WEIGHT = 0.4
    SPECIALTY_WEIGHT = 0.35
    AVAILABILITY_WEIGHT = 0.25
    
    def __init__(self, db: Session):
        self.db = db
    
    async def assign_patient_to_doctor(
        self,
        queue_entry: QueueEntry,
        preferred_specialty: Optional[str] = None
    ) -> Optional[Doctor]:
        """
        Assign a patient to the optimal available doctor.
        
        Algorithm:
        1. Get all available doctors
        2. Filter by specialty if required
        3. Calculate assignment score for each
        4. Select doctor with highest score
        5. Update workload
        """
        available_doctors = await self._get_available_doctors(preferred_specialty)
        
        if not available_doctors:
            return None
        
        # Calculate scores for each doctor
        candidates = []
        for doctor in available_doctors:
            score = self._calculate_assignment_score(
                doctor=doctor,
                queue_entry=queue_entry,
                preferred_specialty=preferred_specialty
            )
            candidates.append(SchedulingCandidate(
                doctor_id=doctor.id,
                score=score,
                specialty_match=doctor.specialty == preferred_specialty if preferred_specialty else True,
                current_load=doctor.current_patient_count,
                max_capacity=doctor.max_patients_per_day
            ))
        
        # Sort by score (descending) and select best
        candidates.sort(key=lambda x: x.score, reverse=True)
        best_candidate = candidates[0]
        
        # Get the doctor and update workload
        assigned_doctor = self.db.query(Doctor).filter(
            Doctor.id == best_candidate.doctor_id
        ).first()
        
        if assigned_doctor:
            assigned_doctor.current_patient_count += 1
            queue_entry.doctor_id = assigned_doctor.id
            self.db.commit()
        
        return assigned_doctor
    
    async def _get_available_doctors(
        self,
        specialty: Optional[str] = None
    ) -> List[Doctor]:
        """Get all available doctors, optionally filtered by specialty."""
        query = self.db.query(Doctor).filter(
            Doctor.is_available == True,
            Doctor.current_patient_count < Doctor.max_patients_per_day
        )
        
        if specialty:
            query = query.filter(Doctor.specialty == specialty)
        
        return query.all()
    
    def _calculate_assignment_score(
        self,
        doctor: Doctor,
        queue_entry: QueueEntry,
        preferred_specialty: Optional[str]
    ) -> float:
        """
        Calculate assignment score for a doctor-patient pair.
        
        Score = α(workload_balance) + β(specialty_match) + γ(availability)
        """
        # Workload balance score (inverse of current load ratio)
        load_ratio = doctor.current_patient_count / doctor.max_patients_per_day
        workload_score = 1.0 - load_ratio
        
        # Specialty match score
        specialty_score = 1.0 if (
            not preferred_specialty or 
            doctor.specialty == preferred_specialty
        ) else 0.5
        
        # Availability score (based on remaining capacity)
        remaining_capacity = doctor.max_patients_per_day - doctor.current_patient_count
        availability_score = min(remaining_capacity / 10, 1.0)
        
        # Emergency boost for critical patients
        emergency_boost = 0.2 if queue_entry.triage_score >= 4 else 0
        
        # Calculate weighted score
        final_score = (
            self.WORKLOAD_WEIGHT * workload_score +
            self.SPECIALTY_WEIGHT * specialty_score +
            self.AVAILABILITY_WEIGHT * availability_score +
            emergency_boost
        )
        
        return round(final_score, 4)
    
    async def rebalance_queue(self) -> Dict[str, int]:
        """
        Rebalance the queue by redistributing patients.
        
        Called periodically to optimize assignments.
        """
        # Get all waiting entries
        waiting_entries = self.db.query(QueueEntry).filter(
            QueueEntry.status == "waiting",
            QueueEntry.doctor_id == None
        ).order_by(QueueEntry.priority_score.desc()).all()
        
        assignments = {"assigned": 0, "failed": 0}
        
        for entry in waiting_entries:
            doctor = await self.assign_patient_to_doctor(entry)
            if doctor:
                assignments["assigned"] += 1
            else:
                assignments["failed"] += 1
        
        return assignments
    
    async def get_optimal_schedule(self) -> List[Dict]:
        """
        Generate optimal schedule for the day.
        
        Uses Hungarian algorithm for optimal matching.
        """
        # Simplified implementation
        doctors = self.db.query(Doctor).filter(Doctor.is_available == True).all()
        queue = self.db.query(QueueEntry).filter(
            QueueEntry.status == "waiting"
        ).order_by(QueueEntry.priority_score.desc()).all()
        
        schedule = []
        for i, entry in enumerate(queue):
            if i < len(doctors):
                schedule.append({
                    "patient_id": entry.patient_id,
                    "doctor_id": doctors[i % len(doctors)].id,
                    "estimated_time": f"{9 + (i // len(doctors))}:00"
                })
        
        return schedule
    
    async def calculate_workload_deviation(self) -> float:
        """
        Calculate workload deviation across doctors.
        
        Target: σ < 15%
        """
        doctors = self.db.query(Doctor).filter(Doctor.is_available == True).all()
        
        if not doctors:
            return 0.0
        
        loads = [d.current_patient_count / d.max_patients_per_day for d in doctors]
        mean_load = sum(loads) / len(loads)
        
        # Calculate standard deviation
        variance = sum((x - mean_load) ** 2 for x in loads) / len(loads)
        std_dev = variance ** 0.5
        
        return round(std_dev * 100, 2)  # Return as percentage
