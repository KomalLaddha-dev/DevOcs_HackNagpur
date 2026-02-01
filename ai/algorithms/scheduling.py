"""
Doctor Scheduling Optimization using Greedy Algorithm

Optimizes patient-doctor assignments to:
1. Minimize average wait time
2. Balance doctor workload (σ < 15%)
3. Match patient needs to doctor specialties
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class Doctor:
    """Doctor entity for scheduling."""
    id: int
    name: str
    specialty: str
    max_patients: int
    current_load: int = 0
    is_available: bool = True


@dataclass
class Patient:
    """Patient entity for scheduling."""
    id: int
    priority_score: float
    required_specialty: Optional[str] = None
    triage_score: int = 3


@dataclass
class Assignment:
    """Patient-Doctor assignment result."""
    patient_id: int
    doctor_id: int
    assignment_score: float
    specialty_match: bool


class GreedyScheduler:
    """
    Greedy scheduling algorithm for patient-doctor assignment.
    
    Algorithm:
    1. Sort patients by priority (descending)
    2. For each patient:
       a. Find eligible doctors
       b. Calculate assignment score for each
       c. Assign to best-scoring doctor
    3. Return assignment matrix
    """
    
    # Scoring weights
    WORKLOAD_WEIGHT = 0.40
    SPECIALTY_WEIGHT = 0.35
    AVAILABILITY_WEIGHT = 0.25
    
    def __init__(self):
        self.doctors: List[Doctor] = []
        self.patients: List[Patient] = []
    
    def set_doctors(self, doctors: List[Doctor]):
        """Set available doctors."""
        self.doctors = doctors
    
    def set_patients(self, patients: List[Patient]):
        """Set patients to be scheduled."""
        self.patients = patients
    
    def optimize(self) -> List[Assignment]:
        """
        Run greedy optimization to assign patients to doctors.
        
        Returns list of assignments.
        """
        # Sort patients by priority (highest first)
        sorted_patients = sorted(
            self.patients, 
            key=lambda p: p.priority_score, 
            reverse=True
        )
        
        assignments = []
        
        for patient in sorted_patients:
            # Find eligible doctors
            eligible = self._get_eligible_doctors(patient)
            
            if not eligible:
                continue
            
            # Calculate scores and find best match
            best_doctor = None
            best_score = -1
            
            for doctor in eligible:
                score = self._calculate_assignment_score(doctor, patient)
                if score > best_score:
                    best_score = score
                    best_doctor = doctor
            
            if best_doctor:
                # Create assignment
                assignment = Assignment(
                    patient_id=patient.id,
                    doctor_id=best_doctor.id,
                    assignment_score=best_score,
                    specialty_match=(
                        patient.required_specialty is None or
                        patient.required_specialty == best_doctor.specialty
                    )
                )
                assignments.append(assignment)
                
                # Update doctor load
                best_doctor.current_load += 1
        
        return assignments
    
    def _get_eligible_doctors(self, patient: Patient) -> List[Doctor]:
        """Get doctors eligible to see this patient."""
        eligible = []
        
        for doctor in self.doctors:
            # Check availability
            if not doctor.is_available:
                continue
            
            # Check capacity
            if doctor.current_load >= doctor.max_patients:
                continue
            
            # Specialty preference (not strict)
            eligible.append(doctor)
        
        # Sort by specialty match first
        if patient.required_specialty:
            eligible.sort(
                key=lambda d: d.specialty == patient.required_specialty,
                reverse=True
            )
        
        return eligible
    
    def _calculate_assignment_score(
        self, 
        doctor: Doctor, 
        patient: Patient
    ) -> float:
        """
        Calculate assignment score for doctor-patient pair.
        
        Score = α(workload) + β(specialty) + γ(availability)
        """
        # Workload balance (inverse of load ratio)
        load_ratio = doctor.current_load / doctor.max_patients
        workload_score = 1.0 - load_ratio
        
        # Specialty match
        specialty_match = (
            patient.required_specialty is None or
            patient.required_specialty == doctor.specialty
        )
        specialty_score = 1.0 if specialty_match else 0.5
        
        # Availability (remaining capacity)
        remaining = doctor.max_patients - doctor.current_load
        availability_score = min(remaining / 10, 1.0)
        
        # Emergency boost
        emergency_boost = 0.15 if patient.triage_score >= 4 else 0
        
        # Weighted sum
        score = (
            self.WORKLOAD_WEIGHT * workload_score +
            self.SPECIALTY_WEIGHT * specialty_score +
            self.AVAILABILITY_WEIGHT * availability_score +
            emergency_boost
        )
        
        return round(score, 4)
    
    def calculate_workload_deviation(self) -> float:
        """
        Calculate standard deviation of doctor workloads.
        
        Target: σ < 15%
        """
        if not self.doctors:
            return 0.0
        
        loads = [
            d.current_load / d.max_patients 
            for d in self.doctors 
            if d.is_available
        ]
        
        if not loads:
            return 0.0
        
        return float(np.std(loads) * 100)
    
    def get_optimization_metrics(self) -> Dict:
        """Get metrics about the scheduling optimization."""
        total_capacity = sum(d.max_patients for d in self.doctors if d.is_available)
        total_load = sum(d.current_load for d in self.doctors if d.is_available)
        
        return {
            "total_doctors": len([d for d in self.doctors if d.is_available]),
            "total_capacity": total_capacity,
            "current_load": total_load,
            "utilization_rate": round(total_load / total_capacity * 100, 1) if total_capacity else 0,
            "workload_deviation": round(self.calculate_workload_deviation(), 2),
            "is_balanced": self.calculate_workload_deviation() < 15
        }


def run_scheduling_example():
    """Example usage of the scheduler."""
    scheduler = GreedyScheduler()
    
    # Sample doctors
    doctors = [
        Doctor(1, "Dr. Smith", "general", 20),
        Doctor(2, "Dr. Johnson", "cardiology", 15),
        Doctor(3, "Dr. Williams", "general", 20),
        Doctor(4, "Dr. Brown", "neurology", 12),
    ]
    
    # Sample patients
    patients = [
        Patient(101, 85.5, "cardiology", 4),
        Patient(102, 72.3, "general", 3),
        Patient(103, 95.0, None, 5),  # Emergency
        Patient(104, 45.2, "general", 2),
        Patient(105, 68.9, "neurology", 3),
    ]
    
    scheduler.set_doctors(doctors)
    scheduler.set_patients(patients)
    
    assignments = scheduler.optimize()
    metrics = scheduler.get_optimization_metrics()
    
    return assignments, metrics


if __name__ == "__main__":
    assignments, metrics = run_scheduling_example()
    
    print("Assignments:")
    for a in assignments:
        print(f"  Patient {a.patient_id} → Doctor {a.doctor_id} (score: {a.assignment_score})")
    
    print(f"\nMetrics: {metrics}")
