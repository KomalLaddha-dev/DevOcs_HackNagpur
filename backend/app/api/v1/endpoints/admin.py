"""
Admin Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.db.session import get_db
from app.schemas.admin import AnalyticsResponse, SystemSettings, AuditLog
from app.services.admin_service import AdminService
from app.api.deps import get_current_admin

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    date_from: date = None,
    date_to: date = None,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics."""
    admin_service = AdminService(db)
    return await admin_service.get_analytics(date_from, date_to)


@router.get("/reports")
async def generate_reports(
    report_type: str,
    date_from: date = None,
    date_to: date = None,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Generate various reports."""
    admin_service = AdminService(db)
    return await admin_service.generate_report(report_type, date_from, date_to)


@router.get("/settings", response_model=SystemSettings)
async def get_settings(
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get system settings."""
    admin_service = AdminService(db)
    return await admin_service.get_settings()


@router.put("/settings", response_model=SystemSettings)
async def update_settings(
    settings: SystemSettings,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update system settings."""
    admin_service = AdminService(db)
    return await admin_service.update_settings(settings)


@router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get system audit logs."""
    admin_service = AdminService(db)
    return await admin_service.get_audit_logs(page, limit)


@router.get("/users")
async def list_users(
    role: str = None,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users."""
    admin_service = AdminService(db)
    return await admin_service.list_users(role)


@router.get("/queue/stats")
async def get_queue_statistics(
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get queue statistics."""
    admin_service = AdminService(db)
    return await admin_service.get_queue_stats()
