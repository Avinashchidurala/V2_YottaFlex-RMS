from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/dispositions")


@router.post("", response_model=schemas.InventoryDispositionResponse, status_code=201)
def create_disposition(payload: schemas.InventoryDispositionCreate, db: Session = Depends(get_db)):
    inspection = db.query(models.Inspection).filter(
        models.Inspection.inspection_id == payload.inspection_id
    ).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    obj = models.InventoryDisposition(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=schemas.PaginatedResponse)
def list_dispositions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    action: Optional[str] = None,
    inspection_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.InventoryDisposition)
    if action:
        q = q.filter(models.InventoryDisposition.action == action)
    if inspection_id:
        q = q.filter(models.InventoryDisposition.inspection_id == inspection_id)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)


@router.get("/{disposition_id}", response_model=schemas.InventoryDispositionResponse)
def get_disposition(disposition_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.InventoryDisposition).filter(
        models.InventoryDisposition.disposition_id == disposition_id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Disposition not found")
    return obj


@router.put("/{disposition_id}", response_model=schemas.InventoryDispositionResponse)
def update_disposition(disposition_id: str, payload: schemas.InventoryDispositionBase, db: Session = Depends(get_db)):
    obj = db.query(models.InventoryDisposition).filter(
        models.InventoryDisposition.disposition_id == disposition_id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Disposition not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{disposition_id}", status_code=204)
def delete_disposition(disposition_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.InventoryDisposition).filter(
        models.InventoryDisposition.disposition_id == disposition_id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Disposition not found")
    db.delete(obj)
    db.commit()
