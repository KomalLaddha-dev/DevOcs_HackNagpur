"""
Patient Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate, SymptomSubmission
from app.services.patient_service import PatientService
from app.api.deps import get_current_patient

router = APIRouter()


@router.get("/me", response_model=PatientResponse)
async def get_current_patient_profile(
    current_patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Get current patient's profile."""
    return current_patient


@router.put("/me", response_model=PatientResponse)
async def update_patient_profile(
    patient_data: PatientUpdate,
    current_patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Update current patient's profile."""
    patient_service = PatientService(db)
    return await patient_service.update(current_patient.id, patient_data)


@router.post("/symptoms", response_model=dict)
async def submit_symptoms(
    symptoms: SymptomSubmission,
    current_patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Submit symptoms for AI triage assessment."""
    patient_service = PatientService(db)
    return await patient_service.submit_symptoms(current_patient.id, symptoms)


@router.get("/queue-status")
async def get_queue_status(
    current_patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Get current patient's position in queue."""
    patient_service = PatientService(db)
    return await patient_service.get_queue_status(current_patient.id)


@router.get("/appointments", response_model=List[dict])
async def get_patient_appointments(
    current_patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Get patient's appointment history."""
    patient_service = PatientService(db)
    return await patient_service.get_appointments(current_patient.id)


@router.get("/health-records")
async def get_health_records(
    current_patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Get patient's digital health records."""
    patient_service = PatientService(db)
    return await patient_service.get_health_records(current_patient.id)
