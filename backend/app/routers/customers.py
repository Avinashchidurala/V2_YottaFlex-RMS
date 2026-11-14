from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/customers")


@router.post("", response_model=schemas.CustomerResponse, status_code=201)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Customer).filter(models.Customer.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    obj = models.Customer(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=schemas.PaginatedResponse)
def list_customers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Customer)
    if tier:
        q = q.filter(models.Customer.tier == tier)
    if is_active is not None:
        q = q.filter(models.Customer.is_active == is_active)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)


@router.get("/{customer_id}", response_model=schemas.CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    return obj


@router.put("/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(customer_id: str, payload: schemas.CustomerBase, db: Session = Depends(get_db)):
    obj = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(obj)
    db.commit()
