"""Alerts router — list alerts, create alert rules, mark as read."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Alert, Product
from app.schemas import (
    AlertResponse,
    AlertListResponse,
    AlertRuleCreate,
    AlertMarkReadRequest,
    MessageResponse,
)
from app.auth import verify_clerk_token

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: HIGH, MEDIUM, LOW"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    product_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(verify_clerk_token),
):
    """List alerts with optional filtering."""
    query = db.query(Alert).filter(Alert.user_id == current_user_id)

    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if alert_type:
        query = query.filter(Alert.type == alert_type)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    if product_id:
        query = query.filter(Alert.product_id == product_id)

    total = query.count()
    unread_count = query.filter(Alert.is_read == False).count()

    # Re-query without the unread filter for the full list
    query = db.query(Alert).filter(Alert.user_id == current_user_id)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if alert_type:
        query = query.filter(Alert.type == alert_type)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    if product_id:
        query = query.filter(Alert.product_id == product_id)

    alerts = query.order_by(desc(Alert.created_at)).offset(offset).limit(limit).all()

    return AlertListResponse(
        alerts=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        unread_count=unread_count,
    )


@router.post("/rules", response_model=AlertResponse)
def create_alert_rule(rule: AlertRuleCreate, db: Session = Depends(get_db), current_user_id: str = Depends(verify_clerk_token)):
    """Create a manual alert/rule."""
    if rule.product_id:
        product = db.query(Product).filter(Product.id == rule.product_id, Product.user_id == current_user_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

    alert = Alert(
        user_id=current_user_id,
        product_id=rule.product_id,
        type=rule.type,
        severity=rule.severity,
        title=rule.title,
        message=rule.message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.put("/mark-read", response_model=MessageResponse)
def mark_alerts_read(request: AlertMarkReadRequest, db: Session = Depends(get_db), current_user_id: str = Depends(verify_clerk_token)):
    """Mark multiple alerts as read."""
    updated = (
        db.query(Alert)
        .filter(Alert.id.in_(request.alert_ids), Alert.user_id == current_user_id)
        .update({Alert.is_read: True}, synchronize_session="fetch")
    )
    db.commit()
    return MessageResponse(message=f"Marked {updated} alert(s) as read.")


@router.put("/{alert_id}/read", response_model=AlertResponse)
def mark_single_alert_read(alert_id: UUID, db: Session = Depends(get_db), current_user_id: str = Depends(verify_clerk_token)):
    """Mark a single alert as read."""
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", response_model=MessageResponse)
def delete_alert(alert_id: UUID, db: Session = Depends(get_db), current_user_id: str = Depends(verify_clerk_token)):
    """Delete a single alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    db.delete(alert)
    db.commit()
    return MessageResponse(message="Alert deleted.")
