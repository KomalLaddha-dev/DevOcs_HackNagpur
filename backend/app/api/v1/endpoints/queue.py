"""
Queue Management Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.queue import QueueEntry, QueueStatus, CheckInRequest
from app.services.queue_service import QueueService
from app.api.deps import get_current_user, get_current_admin

router = APIRouter()


@router.get("/", response_model=List[QueueEntry])
async def get_queue(db: Session = Depends(get_db)):
    """Get current queue status (public view)."""
    queue_service = QueueService(db)
    return await queue_service.get_queue()


@router.post("/checkin", response_model=QueueEntry)
async def check_in(
    checkin_data: CheckInRequest,
    db: Session = Depends(get_db)
):
    """Patient check-in to the queue."""
    queue_service = QueueService(db)
    return await queue_service.check_in(checkin_data)


@router.get("/position/{patient_id}", response_model=QueueStatus)
async def get_queue_position(patient_id: int, db: Session = Depends(get_db)):
    """Get specific patient's queue position."""
    queue_service = QueueService(db)
    return await queue_service.get_position(patient_id)


@router.post("/emergency", response_model=QueueEntry)
async def emergency_override(
    patient_id: int,
    reason: str,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Emergency override - move patient to front of queue."""
    queue_service = QueueService(db)
    return await queue_service.emergency_override(patient_id, reason)


@router.post("/call-next")
async def call_next_patient(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """Call the next patient in queue for a specific doctor."""
    queue_service = QueueService(db)
    return await queue_service.call_next(doctor_id)


@router.websocket("/ws")
async def queue_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket for real-time queue updates."""
    await websocket.accept()
    queue_service = QueueService(db)
    await queue_service.subscribe_to_updates(websocket)
