"""
Demo Data Seeder for SMARTCARE Hackathon Demo
Run this script to populate the system with sample patients for demonstration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timedelta
import random
import uuid

# Sample patient data for demo
DEMO_PATIENTS = [
    {
        "name": "John Smith",
        "age": 72,
        "symptoms": ["chest_pain", "shortness_of_breath", "dizziness"],
        "chronic_conditions": ["heart_disease", "diabetes"],
        "department": "cardiology",
        "duration_hours": 1
    },
    {
        "name": "Maria Garcia",
        "age": 35,
        "symptoms": ["severe_bleeding", "abdominal_pain"],
        "chronic_conditions": [],
        "department": "emergency",
        "duration_hours": 0.5
    },
    {
        "name": "Baby Emma Wilson",
        "age": 2,
        "symptoms": ["high_fever", "difficulty_breathing", "lethargy"],
        "chronic_conditions": ["asthma"],
        "department": "pediatrics",
        "duration_hours": 4
    },
    {
        "name": "Robert Johnson",
        "age": 45,
        "symptoms": ["headache", "fatigue", "mild_fever"],
        "chronic_conditions": [],
        "department": "general",
        "duration_hours": 24
    },
    {
        "name": "Sarah Davis",
        "age": 28,
        "symptoms": ["cough", "sore_throat", "runny_nose"],
        "chronic_conditions": [],
        "department": "general",
        "duration_hours": 48
    },
    {
        "name": "Michael Brown",
        "age": 65,
        "symptoms": ["confusion", "severe_headache", "vision_problems"],
        "chronic_conditions": ["hypertension", "diabetes"],
        "department": "neurology",
        "duration_hours": 2
    },
    {
        "name": "Jennifer Lee",
        "age": 55,
        "symptoms": ["joint_pain", "swelling", "stiffness"],
        "chronic_conditions": ["arthritis"],
        "department": "orthopedics",
        "duration_hours": 72
    },
    {
        "name": "David Martinez",
        "age": 40,
        "symptoms": ["nausea", "abdominal_pain", "vomiting"],
        "chronic_conditions": [],
        "department": "general",
        "duration_hours": 6
    },
    {
        "name": "Emily Thompson",
        "age": 8,
        "symptoms": ["ear_pain", "fever", "irritability"],
        "chronic_conditions": [],
        "department": "pediatrics",
        "duration_hours": 12
    },
    {
        "name": "James Wilson",
        "age": 78,
        "symptoms": ["chest_tightness", "irregular_heartbeat", "fatigue"],
        "chronic_conditions": ["heart_disease", "copd"],
        "department": "cardiology",
        "duration_hours": 3
    },
    {
        "name": "Lisa Anderson",
        "age": 32,
        "symptoms": ["skin_rash", "itching", "mild_fever"],
        "chronic_conditions": ["allergies"],
        "department": "general",
        "duration_hours": 24
    },
    {
        "name": "Christopher Taylor",
        "age": 50,
        "symptoms": ["back_pain", "numbness", "weakness"],
        "chronic_conditions": [],
        "department": "orthopedics",
        "duration_hours": 48
    }
]


def create_demo_queue_entries():
    """Generate demo queue entries for testing"""
    from app.services.triage_engine import perform_triage
    from app.services.priority_queue import priority_queue
    from app.services.crowd_manager import crowd_manager
    
    print("\n" + "="*60)
    print("🏥 SMARTCARE Demo Data Seeder")
    print("="*60 + "\n")
    
    results = []
    
    for i, patient in enumerate(DEMO_PATIENTS):
        print(f"[{i+1}/{len(DEMO_PATIENTS)}] Processing: {patient['name']}")
        
        # Perform triage
        triage_result = perform_triage(
            symptoms=patient['symptoms'],
            age=patient['age'],
            chronic_conditions=patient['chronic_conditions'],
            symptom_duration_hours=patient['duration_hours']
        )
        
        # Create queue entry
        entry_id = str(uuid.uuid4())[:8]
        check_in_time = datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
        
        entry = {
            'entry_id': entry_id,
            'patient_id': f"DEMO-{i+1:03d}",
            'patient_name': patient['name'],
            'age': patient['age'],
            'symptoms': patient['symptoms'],
            'chronic_conditions': patient['chronic_conditions'],
            'severity': triage_result['severity'],
            'severity_description': triage_result['severity_description'],
            'priority_score': triage_result['priority_score'],
            'triage_explanation': triage_result['explanation'],
            'department': patient['department'],
            'check_in_time': check_in_time.isoformat(),
            'teleconsult_eligible': triage_result['teleconsult_eligible']
        }
        
        # Add to priority queue
        priority_queue.push(entry)
        
        # Update crowd manager
        crowd_manager.record_checkin(patient['department'])
        
        results.append({
            'name': patient['name'],
            'severity': triage_result['severity'],
            'score': triage_result['priority_score'],
            'department': patient['department']
        })
        
        print(f"   ✓ Severity: {triage_result['severity']}, Score: {triage_result['priority_score']:.1f}")
    
    print("\n" + "="*60)
    print("📊 Demo Data Summary")
    print("="*60)
    
    # Print summary by severity
    severity_counts = {}
    for r in results:
        sev = r['severity']
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    for sev, count in sorted(severity_counts.items()):
        print(f"   {sev}: {count} patients")
    
    print(f"\n   Total patients added: {len(results)}")
    print("\n✅ Demo data seeding complete!")
    print("="*60 + "\n")
    
    return results


def print_queue_status():
    """Print current queue status"""
    from app.services.priority_queue import priority_queue
    
    stats = priority_queue.get_stats()
    print("\n📋 Current Queue Status:")
    print(f"   Total in queue: {stats['total_in_queue']}")
    print(f"   Critical: {stats['critical_count']}")
    print(f"   High: {stats['high_count']}")
    print(f"   Medium: {stats['medium_count']}")
    print(f"   Low: {stats['low_count']}")


if __name__ == "__main__":
    print("\n🚀 Starting Demo Data Seeder...\n")
    
    try:
        create_demo_queue_entries()
        print_queue_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure to run this from the backend directory:")
        print("   cd backend && python -m app.scripts.seed_demo_data")
