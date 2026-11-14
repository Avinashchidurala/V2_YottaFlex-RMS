from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/inspections")


# ── ReturnShipment ────────────────────────────────────────────────────────────

@router.post("/shipments", response_model=schemas.ReturnShipmentResponse, status_code=201)
def create_shipment(payload: schemas.ReturnShipmentCreate, db: Session = Depends(get_db)):
    auth = db.query(models.ReturnAuthorization).filter(
        models.ReturnAuthorization.auth_id == payload.auth_id
    ).first()
    if not auth:
        raise HTTPException(status_code=404, detail="Authorization not found")
    if auth.auth_status != models.AuthStatus.active:
        raise HTTPException(status_code=400, detail="Authorization is not active")
    obj = models.ReturnShipment(**payload.model_dump())
    db.add(obj)
    # Mark auth as used
    auth.auth_status = models.AuthStatus.used
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/shipments", response_model=schemas.PaginatedResponse)
def list_shipments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.ReturnShipment)
    if status:
        q = q.filter(models.ReturnShipment.status == status)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)


@router.get("/shipments/{shipment_id}", response_model=schemas.ReturnShipmentResponse)
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.ReturnShipment).filter(models.ReturnShipment.shipment_id == shipment_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return obj


@router.put("/shipments/{shipment_id}", response_model=schemas.ReturnShipmentResponse)
def update_shipment(shipment_id: str, payload: schemas.ReturnShipmentBase, db: Session = Depends(get_db)):
    obj = db.query(models.ReturnShipment).filter(models.ReturnShipment.shipment_id == shipment_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Shipment not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


# ── Inspection ────────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.InspectionResponse, status_code=201)
def create_inspection(payload: schemas.InspectionCreate, db: Session = Depends(get_db)):
    shipment = db.query(models.ReturnShipment).filter(
        models.ReturnShipment.shipment_id == payload.shipment_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if shipment.status != models.ShipmentStatus.received:
        raise HTTPException(status_code=400, detail="Shipment must be received before inspection")
    existing = db.query(models.Inspection).filter(
        models.Inspection.shipment_id == payload.shipment_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Inspection already exists for this shipment")
    obj = models.Inspection(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=schemas.PaginatedResponse)
def list_inspections(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    recommended_action: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Inspection)
    if recommended_action:
        q = q.filter(models.Inspection.recommended_action == recommended_action)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)


@router.get("/{inspection_id}", response_model=schemas.InspectionResponse)
def get_inspection(inspection_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Inspection).filter(models.Inspection.inspection_id == inspection_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return obj


@router.put("/{inspection_id}", response_model=schemas.InspectionResponse)
def update_inspection(inspection_id: str, payload: schemas.InspectionBase, db: Session = Depends(get_db)):
    obj = db.query(models.Inspection).filter(models.Inspection.inspection_id == inspection_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Inspection not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{inspection_id}", status_code=204)
def delete_inspection(inspection_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Inspection).filter(models.Inspection.inspection_id == inspection_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Inspection not found")
    db.delete(obj)
    db.commit()
