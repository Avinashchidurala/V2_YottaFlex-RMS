from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
import uuid

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/returns")


def _log_transition(db: Session, entity_type: str, entity_id: str,
                    from_status: Optional[str], to_status: str,
                    changed_by: str, reason: Optional[str] = None):
    log = models.StateTransitionLog(
        log_id=str(uuid.uuid4()),
        entity_type=entity_type,
        entity_id=entity_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        changed_at=datetime.utcnow(),
        reason=reason,
    )
    db.add(log)


# ── ReturnRequest CRUD ────────────────────────────────────────────────────────

@router.post("", response_model=schemas.ReturnRequestResponse, status_code=201)
def create_return_request(payload: schemas.ReturnRequestCreate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    obj = models.ReturnRequest(**payload.model_dump())
    db.add(obj)
    _log_transition(db, "ReturnRequest", payload.request_id, None, "pending", "system")
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=schemas.PaginatedResponse)
def list_return_requests(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    order_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.ReturnRequest)
    if status:
        q = q.filter(models.ReturnRequest.status == status)
    if customer_id:
        q = q.filter(models.ReturnRequest.customer_id == customer_id)
    if order_id:
        q = q.filter(models.ReturnRequest.order_id == order_id)
    total = q.count()
    items = q.order_by(models.ReturnRequest.request_date.desc()).offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)


@router.get("/{request_id}", response_model=schemas.ReturnRequestResponse)
def get_return_request(request_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.ReturnRequest).filter(models.ReturnRequest.request_id == request_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="ReturnRequest not found")
    return obj


@router.put("/{request_id}", response_model=schemas.ReturnRequestResponse)
def update_return_request(request_id: str, payload: schemas.ReturnRequestBase, db: Session = Depends(get_db)):
    obj = db.query(models.ReturnRequest).filter(models.ReturnRequest.request_id == request_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="ReturnRequest not found")
    old_status = str(obj.status.value) if obj.status else None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    if str(obj.status.value) != old_status:
        _log_transition(db, "ReturnRequest", request_id, old_status, str(obj.status.value), "operator")
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{request_id}", status_code=204)
def delete_return_request(request_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.ReturnRequest).filter(models.ReturnRequest.request_id == request_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="ReturnRequest not found")
    db.delete(obj)
    db.commit()


# ── Approve / Reject ──────────────────────────────────────────────────────────

@router.post("/{request_id}/approve", response_model=schemas.ReturnAuthorizationResponse)
def approve_return(
    request_id: str,
    authorized_by: str = Body(..., embed=True),
    override_reason: Optional[str] = Body(default=None, embed=True),
    db: Session = Depends(get_db),
):
    rr = db.query(models.ReturnRequest).filter(models.ReturnRequest.request_id == request_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="ReturnRequest not found")
    if rr.status not in [models.ReturnRequestStatus.pending]:
        raise HTTPException(status_code=400, detail=f"Cannot approve a request in status: {rr.status}")

    # Update all pending lines to approved
    for line in rr.return_lines:
        if line.status == models.ReturnLineStatus.pending:
            line.approved_qty = line.requested_qty
            line.status = models.ReturnLineStatus.approved

    old_status = str(rr.status.value)
    rr.status = models.ReturnRequestStatus.approved
    if override_reason:
        rr.override_flag = True
        rr.override_reason = override_reason

    _log_transition(db, "ReturnRequest", request_id, old_status, "approved", authorized_by, override_reason)

    # Create authorization
    auth_id = f"AUTH-{request_id}"
    authorized_at = datetime.utcnow()
    expiry = (authorized_at + timedelta(days=14)).date()
    auth = models.ReturnAuthorization(
        auth_id=auth_id,
        request_id=request_id,
        authorized_by=authorized_by,
        authorized_at=authorized_at,
        expiry_date=expiry,
        auth_status=models.AuthStatus.active,
    )
    db.add(auth)
    _log_transition(db, "ReturnAuthorization", auth_id, None, "active", authorized_by)
    db.commit()
    db.refresh(auth)
    return auth


@router.post("/{request_id}/reject", response_model=schemas.ReturnRequestResponse)
def reject_return(
    request_id: str,
    rejected_by: str = Body(..., embed=True),
    rejection_reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    rr = db.query(models.ReturnRequest).filter(models.ReturnRequest.request_id == request_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="ReturnRequest not found")
    if rr.status not in [models.ReturnRequestStatus.pending]:
        raise HTTPException(status_code=400, detail=f"Cannot reject a request in status: {rr.status}")

    old_status = str(rr.status.value)
    rr.status = models.ReturnRequestStatus.rejected
    rr.notes = (rr.notes or "") + f"\nRejected: {rejection_reason}"
    for line in rr.return_lines:
        if line.status == models.ReturnLineStatus.pending:
            line.status = models.ReturnLineStatus.rejected
            line.rejection_reason = rejection_reason

    _log_transition(db, "ReturnRequest", request_id, old_status, "rejected", rejected_by, rejection_reason)
    db.commit()
    db.refresh(rr)
    return rr


# ── ReturnLine CRUD ───────────────────────────────────────────────────────────

@router.post("/{request_id}/lines", response_model=schemas.ReturnLineResponse, status_code=201)
def add_return_line(request_id: str, payload: schemas.ReturnLineCreate, db: Session = Depends(get_db)):
    rr = db.query(models.ReturnRequest).filter(models.ReturnRequest.request_id == request_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="ReturnRequest not found")
    obj = models.ReturnLine(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{request_id}/lines", response_model=List[schemas.ReturnLineResponse])
def list_return_lines(request_id: str, db: Session = Depends(get_db)):
    return db.query(models.ReturnLine).filter(models.ReturnLine.request_id == request_id).all()


# ── ReturnAuthorization ────────────────────────────────────────────────────────

@router.get("/{request_id}/authorization", response_model=schemas.ReturnAuthorizationResponse)
def get_authorization(request_id: str, db: Session = Depends(get_db)):
    auth = db.query(models.ReturnAuthorization).filter(
        models.ReturnAuthorization.request_id == request_id
    ).first()
    if not auth:
        raise HTTPException(status_code=404, detail="Authorization not found")
    return auth


@router.get("/authorizations/all", response_model=schemas.PaginatedResponse)
def list_authorizations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(models.ReturnAuthorization)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)
