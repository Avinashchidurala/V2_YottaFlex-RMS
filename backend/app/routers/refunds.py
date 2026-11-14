from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/refunds")


def _detect_duplicate(db: Session, request_id: str, refund_id: str) -> Optional[str]:
    """Return the existing refund_id if a processed refund already exists for this request."""
    existing = db.query(models.Refund).filter(
        models.Refund.request_id == request_id,
        models.Refund.status == models.RefundStatus.processed,
        models.Refund.refund_id != refund_id,
    ).first()
    return existing.refund_id if existing else None


@router.post("", response_model=schemas.RefundResponse, status_code=201)
def create_refund(payload: schemas.RefundCreate, db: Session = Depends(get_db)):
    rr = db.query(models.ReturnRequest).filter(models.ReturnRequest.request_id == payload.request_id).first()
    if not rr:
        raise HTTPException(status_code=404, detail="ReturnRequest not found")

    # Duplicate detection
    dup_id = _detect_duplicate(db, payload.request_id, payload.refund_id)
    data = payload.model_dump()
    if dup_id:
        data["is_duplicate"] = True
        data["duplicate_of_refund_id"] = dup_id
        data["status"] = models.RefundStatus.duplicate.value

    obj = models.Refund(**data)
    db.add(obj)

    if dup_id:
        anomaly = models.AnomalyRecord(
            anomaly_id=__import__("uuid").uuid4().__str__(),
            entity_type="Refund",
            entity_id=payload.refund_id,
            issue_type=models.AnomalyIssueType.duplicate_refund,
            ground_truth_label=True,
            detected_at=datetime.utcnow(),
            details_json=f'{{"duplicate_of": "{dup_id}", "request_id": "{payload.request_id}"}}',
        )
        db.add(anomaly)

    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=schemas.PaginatedResponse)
def list_refunds(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    status: Optional[str] = None,
    request_id: Optional[str] = None,
    is_duplicate: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Refund)
    if status:
        q = q.filter(models.Refund.status == status)
    if request_id:
        q = q.filter(models.Refund.request_id == request_id)
    if is_duplicate is not None:
        q = q.filter(models.Refund.is_duplicate == is_duplicate)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)


@router.get("/{refund_id}", response_model=schemas.RefundResponse)
def get_refund(refund_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Refund).filter(models.Refund.refund_id == refund_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Refund not found")
    return obj


@router.put("/{refund_id}", response_model=schemas.RefundResponse)
def update_refund(refund_id: str, payload: schemas.RefundBase, db: Session = Depends(get_db)):
    obj = db.query(models.Refund).filter(models.Refund.refund_id == refund_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Refund not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{refund_id}/process", response_model=schemas.RefundResponse)
def process_refund(refund_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Refund).filter(models.Refund.refund_id == refund_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Refund not found")
    if obj.is_duplicate:
        raise HTTPException(status_code=400, detail="Cannot process a duplicate refund")
    if obj.status == models.RefundStatus.processed:
        raise HTTPException(status_code=400, detail="Refund already processed")
    obj.status = models.RefundStatus.processed
    obj.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{refund_id}", status_code=204)
def delete_refund(refund_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Refund).filter(models.Refund.refund_id == refund_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Refund not found")
    db.delete(obj)
    db.commit()
