"""
SmartCare Priority Queue System
================================
Max-heap based priority queue with dynamic recalculation.
NO FIFO - patients are served by medical urgency!

Key Features:
1. Priority Score Calculation (weighted factors)
2. Dynamic Reordering (when new patient arrives or doctor frees up)
3. Fairness Rules (max wait time cap, elderly boost)
4. Emergency Override (instantly move to top)
"""

import heapq
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from app.core.constants import (
    PRIORITY_WEIGHTS, QUEUE_THRESHOLDS, BASE_WAIT_TIMES,
    SEVERITY_DESCRIPTIONS
)


@dataclass(order=True)
class QueueItem:
    """
    Queue item with comparison support for heap operations.
    Uses negative priority for max-heap behavior (Python's heapq is min-heap).
    """
    priority: float = field(compare=True)
    timestamp: datetime = field(compare=True)  # For tie-breaking (FIFO within same priority)
    patient_id: int = field(compare=False)
    entry_id: int = field(compare=False)
    triage_score: int = field(compare=False)
    is_emergency: bool = field(compare=False, default=False)
    
    def to_dict(self) -> Dict:
        return {
            "patient_id": self.patient_id,
            "entry_id": self.entry_id,
            "priority_score": abs(self.priority),  # Convert back to positive
            "triage_score": self.triage_score,
            "is_emergency": self.is_emergency,
            "check_in_time": self.timestamp.isoformat()
        }


class SmartPriorityQueue:
    """
    Priority Queue using Max-Heap for patient scheduling.
    
    Priority Formula:
    =================
    priority_score = (severity × 0.4) + (wait_time_norm × 0.25) 
                   + (age_factor × 0.15) + (chronic_factor × 0.1)
                   + (emergency_boost × 0.1)
    
    Where:
    - severity: 1-5 (from triage)
    - wait_time_norm: normalized waiting time (0-1, increases over time)
    - age_factor: 0-1 (higher for elderly/infants)
    - chronic_factor: 0-1 (higher for chronic conditions)
    - emergency_boost: 0 or 1 (manual override)
    """
    
    def __init__(self):
        self._heap: List[Tuple[float, datetime, QueueItem]] = []
        self._entries: Dict[int, QueueItem] = {}  # entry_id -> QueueItem
        self._removed: set = set()  # Set of removed entry_ids (lazy deletion)
        self._patient_info: Dict[int, Dict] = {}  # entry_id -> patient display info
        self._queue: List = []  # Alias for compatibility
        self._entry_map: Dict[int, QueueItem] = {}  # Alias for compatibility
        self._current_patients: Dict[str, Dict] = {}  # department -> current patient being seen
    
    def calculate_priority_score(
        self,
        triage_score: int,
        wait_minutes: int,
        age_factor: float,
        chronic_factor: float,
        is_emergency: bool
    ) -> float:
        """
        Calculate weighted priority score.
        
        Higher score = higher priority (seen first).
        """
        # Normalize values to 0-1 range
        severity_norm = triage_score / 5.0
        
        # Wait time: cap at max threshold for normalization
        max_wait = QUEUE_THRESHOLDS["max_wait_time_minutes"]
        wait_norm = min(wait_minutes / max_wait, 1.0)
        
        # Age factor already 0-1.5 range, normalize to 0-1
        age_norm = min(age_factor / 1.5, 1.0)
        
        # Chronic factor already 0-1
        chronic_norm = min(chronic_factor, 1.0)
        
        # Emergency is binary
        emergency_norm = 1.0 if is_emergency else 0.0
        
        # Calculate weighted sum
        score = (
            (severity_norm * PRIORITY_WEIGHTS["severity"]) +
            (wait_norm * PRIORITY_WEIGHTS["wait_time"]) +
            (age_norm * PRIORITY_WEIGHTS["age_factor"]) +
            (chronic_norm * PRIORITY_WEIGHTS["chronic_factor"]) +
            (emergency_norm * PRIORITY_WEIGHTS["emergency_flag"])
        )
        
        # Emergency patients get massive boost
        if is_emergency:
            score += 10.0  # Guaranteed top of queue
        
        return round(score, 4)
    
    def push(
        self,
        patient_id: int,
        entry_id: int,
        triage_score: int,
        age_factor: float = 1.0,
        chronic_factor: float = 0.0,
        is_emergency: bool = False,
        check_in_time: datetime = None
    ) -> float:
        """
        Add patient to priority queue.
        
        Returns: calculated priority score
        """
        check_in_time = check_in_time or datetime.utcnow()
        wait_minutes = 0  # Just checked in
        
        priority_score = self.calculate_priority_score(
            triage_score=triage_score,
            wait_minutes=wait_minutes,
            age_factor=age_factor,
            chronic_factor=chronic_factor,
            is_emergency=is_emergency
        )
        
        item = QueueItem(
            priority=-priority_score,  # Negative for max-heap
            timestamp=check_in_time,
            patient_id=patient_id,
            entry_id=entry_id,
            triage_score=triage_score,
            is_emergency=is_emergency
        )
        
        heapq.heappush(self._heap, (item.priority, item.timestamp, item))
        self._entries[entry_id] = item
        
        return priority_score
    
    def pop(self) -> Optional[QueueItem]:
        """
        Remove and return highest priority patient.
        Uses lazy deletion for efficiency.
        """
        while self._heap:
            priority, timestamp, item = heapq.heappop(self._heap)
            
            # Skip if this entry was removed
            if item.entry_id in self._removed:
                self._removed.discard(item.entry_id)
                continue
            
            # Valid entry - remove from tracking
            if item.entry_id in self._entries:
                del self._entries[item.entry_id]
            
            return item
        
        return None
    
    def peek(self) -> Optional[QueueItem]:
        """Get highest priority patient without removing."""
        while self._heap:
            priority, timestamp, item = self._heap[0]
            
            if item.entry_id in self._removed:
                heapq.heappop(self._heap)
                self._removed.discard(item.entry_id)
                continue
            
            return item
        
        return None
    
    def remove(self, entry_id: int) -> bool:
        """Mark entry for lazy deletion."""
        if entry_id in self._entries:
            self._removed.add(entry_id)
            del self._entries[entry_id]
            return True
        return False
    
    def update_priority(
        self,
        entry_id: int,
        new_triage_score: int = None,
        age_factor: float = None,
        chronic_factor: float = None,
        is_emergency: bool = None,
        wait_minutes: int = None
    ) -> Optional[float]:
        """
        Update patient's priority (e.g., when wait time increases).
        Uses lazy deletion + re-insertion for heap property.
        """
        if entry_id not in self._entries:
            return None
        
        old_item = self._entries[entry_id]
        
        # Remove old entry (lazy)
        self._removed.add(entry_id)
        
        # Recalculate with new values
        new_score = self.calculate_priority_score(
            triage_score=new_triage_score or old_item.triage_score,
            wait_minutes=wait_minutes or 0,
            age_factor=age_factor or 1.0,
            chronic_factor=chronic_factor or 0.0,
            is_emergency=is_emergency if is_emergency is not None else old_item.is_emergency
        )
        
        # Re-insert with new priority
        new_item = QueueItem(
            priority=-new_score,
            timestamp=old_item.timestamp,
            patient_id=old_item.patient_id,
            entry_id=entry_id,
            triage_score=new_triage_score or old_item.triage_score,
            is_emergency=is_emergency if is_emergency is not None else old_item.is_emergency
        )
        
        heapq.heappush(self._heap, (new_item.priority, new_item.timestamp, new_item))
        self._entries[entry_id] = new_item
        self._removed.discard(entry_id)
        
        return new_score
    
    def emergency_override(self, entry_id: int) -> Optional[float]:
        """
        Emergency override - instantly move patient to top of queue.
        Returns new priority score.
        """
        return self.update_priority(entry_id, is_emergency=True)
    
    def get_queue_list(self) -> List[Dict]:
        """
        Get sorted list of all patients in queue.
        Does NOT modify the heap.
        """
        # Filter out removed entries
        valid_items = [
            (p, t, item) for p, t, item in self._heap 
            if item.entry_id not in self._removed
        ]
        
        # Sort by priority (already negative, so ascending = highest priority first)
        sorted_items = sorted(valid_items, key=lambda x: (x[0], x[1]))
        
        result = []
        for i, (priority, timestamp, item) in enumerate(sorted_items):
            data = item.to_dict()
            data["position"] = i + 1
            data["severity_info"] = SEVERITY_DESCRIPTIONS.get(item.triage_score, {})
            
            # Add patient display info if available
            if item.entry_id in self._patient_info:
                info = self._patient_info[item.entry_id]
                data["patient_name"] = info.get("name", f"Patient #{item.patient_id}")
                data["age"] = info.get("age", 0)
                data["symptoms"] = info.get("symptoms", [])
                data["chronic_conditions"] = info.get("chronic_conditions", [])
                data["department"] = info.get("department", "general")
                data["severity"] = info.get("severity", "MEDIUM")
                data["triage_explanation"] = info.get("explanation", [])
            else:
                data["patient_name"] = f"Patient #{item.patient_id}"
                data["age"] = 0
                data["symptoms"] = []
                data["chronic_conditions"] = []
                data["department"] = "general"
                data["severity"] = "MEDIUM"
                data["triage_explanation"] = []
                
            result.append(data)
        
        return result
    
    def recalculate_all_priorities(self, current_time: datetime = None) -> int:
        """
        Recalculate priorities for all patients (e.g., for wait time updates).
        Called periodically or when queue needs rebalancing.
        
        Returns: number of entries updated
        """
        current_time = current_time or datetime.utcnow()
        updated = 0
        
        # Get all current entries
        entries_to_update = list(self._entries.items())
        
        for entry_id, item in entries_to_update:
            # Calculate wait time
            wait_minutes = (current_time - item.timestamp).total_seconds() / 60
            
            # Update priority with new wait time
            self.update_priority(
                entry_id=entry_id,
                wait_minutes=int(wait_minutes)
            )
            updated += 1
        
        return updated
    
    def __len__(self) -> int:
        """Number of active entries in queue."""
        return len(self._entries)
    
    def get_stats(self) -> Dict:
        """Get queue statistics."""
        if not self._entries:
            return {
                "total_patients": 0,
                "avg_wait_minutes": 0,
                "critical_count": 0,
                "urgent_count": 0,
                "moderate_count": 0,
                "low_count": 0,
                "minimal_count": 0,
                "emergency_count": 0
            }
        
        now = datetime.utcnow()
        total_wait = 0
        critical_count = 0
        urgent_count = 0
        moderate_count = 0
        low_count = 0
        minimal_count = 0
        emergency_count = 0
        
        for item in self._entries.values():
            wait = (now - item.timestamp).total_seconds() / 60
            total_wait += wait
            
            # Count by severity level using 1-10 scale
            score = item.triage_score
            if score >= 9:
                critical_count += 1
            elif score >= 7:
                urgent_count += 1
            elif score >= 5:
                moderate_count += 1
            elif score >= 3:
                low_count += 1
            else:
                minimal_count += 1
                
            if item.is_emergency:
                emergency_count += 1
        
        return {
            "total_patients": len(self._entries),
            "avg_wait_minutes": round(total_wait / len(self._entries), 1),
            "critical_count": critical_count,
            "urgent_count": urgent_count,
            "moderate_count": moderate_count,
            "low_count": low_count,
            "minimal_count": minimal_count,
            "emergency_count": emergency_count
        }

    def set_current_patient(self, department: str, patient_data: Dict) -> None:
        """Set the current patient being seen for a department."""
        dept_key = department.lower() if department else "general"
        self._current_patients[dept_key] = {
            **patient_data,
            "started_at": datetime.utcnow().isoformat()
        }
    
    def get_current_patient(self, department: str) -> Optional[Dict]:
        """Get the current patient being seen for a department."""
        dept_key = department.lower() if department else "general"
        return self._current_patients.get(dept_key)
    
    def clear_current_patient(self, department: str) -> bool:
        """Clear current patient (consultation complete) for a department."""
        dept_key = department.lower() if department else "general"
        if dept_key in self._current_patients:
            del self._current_patients[dept_key]
            return True
        return False
    
    def get_all_current_patients(self) -> Dict[str, Dict]:
        """Get all current patients being seen across all departments."""
        return self._current_patients.copy()


# Singleton for application-wide queue (can also be per-department)
_global_queue = None

def get_priority_queue() -> SmartPriorityQueue:
    """Get the global priority queue instance."""
    global _global_queue
    if _global_queue is None:
        _global_queue = SmartPriorityQueue()
    return _global_queue
