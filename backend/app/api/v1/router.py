"""
API v1 Router - Aggregates all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, patients, queue, doctors, admin, appointments

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(queue.router, prefix="/queue", tags=["Queue"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
