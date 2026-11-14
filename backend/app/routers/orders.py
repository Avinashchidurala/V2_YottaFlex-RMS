from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/orders")


@router.post("", response_model=schemas.OrderResponse, status_code=201)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    obj = models.Order(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=schemas.PaginatedResponse)
def list_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Order)
    if status:
        q = q.filter(models.Order.status == status)
    if customer_id:
        q = q.filter(models.Order.customer_id == customer_id)
    if date_from:
        q = q.filter(models.Order.order_date >= date_from)
    if date_to:
        q = q.filter(models.Order.order_date <= date_to)
    total = q.count()
    items = q.order_by(models.Order.order_date.desc()).offset(skip).limit(limit).all()
    return schemas.PaginatedResponse(total=total, skip=skip, limit=limit, data=items)


@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Order).filter(models.Order.order_id == order_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return obj


@router.put("/{order_id}", response_model=schemas.OrderResponse)
def update_order(order_id: str, payload: schemas.OrderBase, db: Session = Depends(get_db)):
    obj = db.query(models.Order).filter(models.Order.order_id == order_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Order).filter(models.Order.order_id == order_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(obj)
    db.commit()


# ── Order Lines ───────────────────────────────────────────────────────────────

@router.post("/{order_id}/lines", response_model=schemas.OrderLineResponse, status_code=201)
def add_order_line(order_id: str, payload: schemas.OrderLineCreate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if payload.order_id != order_id:
        raise HTTPException(status_code=400, detail="order_id mismatch")
    obj = models.OrderLine(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{order_id}/lines", response_model=List[schemas.OrderLineResponse])
def list_order_lines(order_id: str, db: Session = Depends(get_db)):
    return db.query(models.OrderLine).filter(models.OrderLine.order_id == order_id).all()


@router.get("/{order_id}/lines/{line_id}", response_model=schemas.OrderLineResponse)
def get_order_line(order_id: str, line_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.OrderLine).filter(
        models.OrderLine.line_id == line_id,
        models.OrderLine.order_id == order_id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Order line not found")
    return obj
