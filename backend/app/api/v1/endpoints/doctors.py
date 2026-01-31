"""
Doctor Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.doctor import DoctorResponse, DoctorSchedule, AvailabilityUpdate
from app.services.doctor_service import DoctorService
from app.api.deps import get_current_doctor

router = APIRouter()


@router.get("/", response_model=List[DoctorResponse])
async def list_doctors(
    specialty: str = None,
    available: bool = None,
    db: Session = Depends(get_db)
):
    """List all doctors with optional filters."""
    doctor_service = DoctorService(db)
    return await doctor_service.list_doctors(specialty=specialty, available=available)


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Get specific doctor details."""
    doctor_service = DoctorService(db)
    return await doctor_service.get_doctor(doctor_id)


@router.get("/{doctor_id}/schedule", response_model=DoctorSchedule)
async def get_doctor_schedule(doctor_id: int, db: Session = Depends(get_db)):
    """Get doctor's schedule."""
    doctor_service = DoctorService(db)
    return await doctor_service.get_schedule(doctor_id)


@router.post("/{doctor_id}/available", response_model=DoctorResponse)
async def update_availability(
    doctor_id: int,
    availability: AvailabilityUpdate,
    current_doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Update doctor's availability status."""
    if current_doctor.id != doctor_id:
        raise HTTPException(status_code=403, detail="Cannot update other doctor's availability")
    
    doctor_service = DoctorService(db)
    return await doctor_service.update_availability(doctor_id, availability)


@router.get("/dashboard/me")
async def get_doctor_dashboard(
    current_doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Get doctor's dashboard data."""
    doctor_service = DoctorService(db)
    return await doctor_service.get_dashboard(current_doctor.id)


@router.get("/{doctor_id}/patients")
async def get_assigned_patients(
    doctor_id: int,
    current_doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Get patients assigned to the doctor."""
    doctor_service = DoctorService(db)
    return await doctor_service.get_assigned_patients(doctor_id)
