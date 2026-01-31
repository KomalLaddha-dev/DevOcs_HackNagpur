"""
Appointment Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.db.session import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.services.appointment_service import AppointmentService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new appointment."""
    appointment_service = AppointmentService(db)
    return await appointment_service.create(appointment_data, current_user.id)


@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    date_from: date = None,
    date_to: date = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List appointments with filters."""
    appointment_service = AppointmentService(db)
    return await appointment_service.list_appointments(date_from, date_to, status)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Get specific appointment details."""
    appointment_service = AppointmentService(db)
    return await appointment_service.get(appointment_id)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an appointment."""
    appointment_service = AppointmentService(db)
    return await appointment_service.update(appointment_id, appointment_data)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an appointment."""
    appointment_service = AppointmentService(db)
    await appointment_service.cancel(appointment_id)


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: int,
    notes: str = None,
    db: Session = Depends(get_db)
):
    """Mark appointment as completed."""
    appointment_service = AppointmentService(db)
    return await appointment_service.complete(appointment_id, notes)
