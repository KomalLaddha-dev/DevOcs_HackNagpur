"""
Queue Service - Core queue management logic
"""

from sqlalchemy.orm import Session
from fastapi import WebSocket
from typing import List, Optional
import heapq
from datetime import datetime

from app.models.queue import QueueEntry
from app.models.patient import Patient
from app.schemas.queue import CheckInRequest, QueueStatus


class PriorityQueue:
    """Custom Priority Queue implementation using max-heap."""
    
    def __init__(self):
        self._queue = []
        self._index = 0
    
    def push(self, priority: float, item):
        # Use negative priority for max-heap behavior
        heapq.heappush(self._queue, (-priority, self._index, item))
        self._index += 1
    
    def pop(self):
        if self._queue:
            return heapq.heappop(self._queue)[-1]
        return None
    
    def peek(self):
        if self._queue:
            return self._queue[0][-1]
        return None
    
    def __len__(self):
        return len(self._queue)


class QueueService:
    """Service for managing patient queue."""
    
    # Weights for priority calculation
    SEVERITY_WEIGHT = 0.4
    WAIT_TIME_WEIGHT = 0.3
    AGE_WEIGHT = 0.15
    CHRONIC_WEIGHT = 0.15
    
    def __init__(self, db: Session):
        self.db = db
        self._priority_queue = PriorityQueue()
        self._websocket_connections: List[WebSocket] = []
    
    async def check_in(self, checkin_data: CheckInRequest) -> QueueEntry:
        """Check in a patient to the queue."""
        # Generate token number
        token = self._generate_token()
        
        # Create queue entry
        entry = QueueEntry(
            patient_id=checkin_data.patient_id,
            appointment_id=checkin_data.appointment_id,
            token_number=token,
            status="waiting"
        )
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        
        # Broadcast update
        await self._broadcast_queue_update()
        
        return entry
    
    async def get_queue(self) -> List[QueueEntry]:
        """Get current queue sorted by priority."""
        entries = self.db.query(QueueEntry).filter(
            QueueEntry.status.in_(["waiting", "called"])
        ).all()
        
        # Sort by priority score (descending)
        sorted_entries = sorted(entries, key=lambda x: x.priority_score, reverse=True)
        
        # Add position to each entry
        for i, entry in enumerate(sorted_entries):
            entry.position = i + 1
        
        return sorted_entries
    
    async def get_position(self, patient_id: int) -> QueueStatus:
        """Get patient's current position in queue."""
        queue = await self.get_queue()
        
        for i, entry in enumerate(queue):
            if entry.patient_id == patient_id:
                return QueueStatus(
                    patient_id=patient_id,
                    token_number=entry.token_number,
                    position=i + 1,
                    estimated_wait_time=self._estimate_wait_time(i + 1),
                    status=entry.status,
                    triage_score=entry.triage_score,
                    priority_score=entry.priority_score,
                    people_ahead=i
                )
        
        return None
    
    def calculate_priority(
        self,
        triage_score: int,
        wait_time_minutes: int,
        age: int,
        has_chronic_condition: bool
    ) -> float:
        """Calculate priority score for a patient."""
        # Normalize values
        normalized_triage = triage_score / 5.0
        normalized_wait = min(wait_time_minutes / 180.0, 1.0)  # Cap at 3 hours
        age_factor = 1.0 + (0.2 if age > 65 or age < 5 else 0)
        chronic_factor = 1.2 if has_chronic_condition else 1.0
        
        priority = (
            self.SEVERITY_WEIGHT * normalized_triage +
            self.WAIT_TIME_WEIGHT * normalized_wait +
            self.AGE_WEIGHT * age_factor +
            self.CHRONIC_WEIGHT * chronic_factor
        )
        
        return round(priority * 100, 2)
    
    async def emergency_override(self, patient_id: int, reason: str) -> QueueEntry:
        """Move patient to front of queue (emergency)."""
        entry = self.db.query(QueueEntry).filter(
            QueueEntry.patient_id == patient_id,
            QueueEntry.status == "waiting"
        ).first()
        
        if entry:
            entry.is_emergency = True
            entry.triage_score = 5
            entry.priority_score = 999.0  # Maximum priority
            self.db.commit()
            
            await self._broadcast_queue_update()
        
        return entry
    
    async def call_next(self, doctor_id: int) -> Optional[QueueEntry]:
        """Call the next patient for a specific doctor."""
        queue = await self.get_queue()
        
        if queue:
            next_patient = queue[0]
            next_patient.status = "called"
            next_patient.called_time = datetime.utcnow()
            next_patient.doctor_id = doctor_id
            self.db.commit()
            
            await self._broadcast_queue_update()
            return next_patient
        
        return None
    
    async def subscribe_to_updates(self, websocket: WebSocket):
        """Subscribe to real-time queue updates."""
        self._websocket_connections.append(websocket)
        try:
            while True:
                await websocket.receive_text()
        except:
            self._websocket_connections.remove(websocket)
    
    async def _broadcast_queue_update(self):
        """Broadcast queue update to all connected clients."""
        queue = await self.get_queue()
        message = {
            "event": "queue:updated",
            "data": [{"token": e.token_number, "position": i+1} for i, e in enumerate(queue)]
        }
        
        for ws in self._websocket_connections:
            try:
                await ws.send_json(message)
            except:
                pass
    
    def _generate_token(self) -> str:
        """Generate unique token number."""
        today = datetime.now().strftime("%Y%m%d")
        count = self.db.query(QueueEntry).filter(
            QueueEntry.token_number.like(f"SC{today}%")
        ).count()
        return f"SC{today}{str(count + 1).zfill(4)}"
    
    def _estimate_wait_time(self, position: int) -> int:
        """Estimate wait time based on position."""
        # Average consultation time: 10 minutes
        return position * 10
