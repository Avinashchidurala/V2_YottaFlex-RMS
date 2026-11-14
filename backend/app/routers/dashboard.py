from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, date
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/dashboard")


@router.get("/overview", response_model=schemas.DashboardOverview)
def get_overview(db: Session = Depends(get_db)):
    total_orders = db.query(func.count(models.Order.order_id)).scalar() or 0
    total_return_requests = db.query(func.count(models.ReturnRequest.request_id)).scalar() or 0
    return_rate_pct = round((total_return_requests / total_orders * 100) if total_orders > 0 else 0.0, 2)

    avg_refund = db.query(func.avg(models.Refund.net_refund_inr)).scalar() or 0.0
    pending_approvals = db.query(func.count(models.ReturnRequest.request_id)).filter(
        models.ReturnRequest.status == models.ReturnRequestStatus.pending
    ).scalar() or 0

    total_refunded = db.query(func.sum(models.Refund.net_refund_inr)).filter(
        models.Refund.status == models.RefundStatus.processed
    ).scalar() or 0.0

    now = datetime.utcnow()
    total_refunded_this_month = db.query(func.sum(models.Refund.net_refund_inr)).filter(
        models.Refund.status == models.RefundStatus.processed,
        extract("year", models.Refund.processed_at) == now.year,
        extract("month", models.Refund.processed_at) == now.month
    ).scalar() or 0.0

    anomaly_count = db.query(func.count(models.AnomalyRecord.anomaly_id)).scalar() or 0

    return schemas.DashboardOverview(
        total_orders=total_orders,
        total_return_requests=total_return_requests,
        return_rate_pct=return_rate_pct,
        avg_refund_amount_inr=round(float(avg_refund), 2),
        pending_approvals=pending_approvals,
        total_refunded_inr=round(float(total_refunded), 2),
        total_refunded_this_month_inr=round(float(total_refunded_this_month), 2),
        anomaly_count=anomaly_count,
    )


@router.get("/return-trends", response_model=List[schemas.ReturnTrend])
def get_return_trends(days: int = 30, db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.date(models.ReturnRequest.request_date).label("day"),
            func.count(models.ReturnRequest.request_id).label("return_count"),
            func.sum(
                func.case(
                    (models.ReturnRequest.status.in_([
                        models.ReturnRequestStatus.approved,
                        models.ReturnRequestStatus.partially_approved
                    ]), 1),
                    else_=0
                )
            ).label("approval_count"),
        )
        .group_by(func.date(models.ReturnRequest.request_date))
        .order_by(func.date(models.ReturnRequest.request_date).desc())
        .limit(days)
        .all()
    )
    return [
        schemas.ReturnTrend(
            date=str(r.day),
            return_count=r.return_count,
            approval_count=int(r.approval_count or 0),
        )
        for r in reversed(rows)
    ]


@router.get("/disposition-breakdown", response_model=List[schemas.DispositionBreakdown])
def get_disposition_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.InventoryDisposition.action,
            func.count(models.InventoryDisposition.disposition_id).label("count"),
            func.sum(models.InventoryDisposition.estimated_recovery_value_inr).label("est_recovery"),
        )
        .group_by(models.InventoryDisposition.action)
        .all()
    )
    return [
        schemas.DispositionBreakdown(
            action=r.action.value if hasattr(r.action, "value") else str(r.action),
            count=r.count,
            estimated_recovery_inr=round(float(r.est_recovery or 0), 2),
        )
        for r in rows
    ]


@router.get("/top-return-reasons", response_model=List[schemas.TopReturnReason])
def get_top_return_reasons(db: Session = Depends(get_db)):
    total = db.query(func.count(models.ReturnRequest.request_id)).scalar() or 1
    rows = (
        db.query(
            models.ReturnRequest.reason,
            func.count(models.ReturnRequest.request_id).label("count"),
        )
        .group_by(models.ReturnRequest.reason)
        .order_by(func.count(models.ReturnRequest.request_id).desc())
        .all()
    )
    return [
        schemas.TopReturnReason(
            reason=r.reason.value if hasattr(r.reason, "value") else str(r.reason),
            count=r.count,
            percentage=round(r.count / total * 100, 2),
        )
        for r in rows
    ]


@router.get("/refund-summary", response_model=schemas.RefundSummary)
def get_refund_summary(db: Session = Depends(get_db)):
    agg = db.query(
        func.sum(models.Refund.gross_refund_inr).label("gross"),
        func.sum(models.Refund.restocking_fee_inr).label("restocking"),
        func.sum(models.Refund.shipping_fee_inr).label("shipping"),
        func.sum(models.Refund.net_refund_inr).label("net"),
        func.avg(models.Refund.net_refund_inr).label("avg_net"),
    ).one()

    pending_count = db.query(func.count(models.Refund.refund_id)).filter(
        models.Refund.status == models.RefundStatus.pending
    ).scalar() or 0

    processed_count = db.query(func.count(models.Refund.refund_id)).filter(
        models.Refund.status == models.RefundStatus.processed
    ).scalar() or 0

    duplicate_count = db.query(func.count(models.Refund.refund_id)).filter(
        models.Refund.is_duplicate == True
    ).scalar() or 0

    return schemas.RefundSummary(
        total_gross_inr=round(float(agg.gross or 0), 2),
        total_restocking_fees_inr=round(float(agg.restocking or 0), 2),
        total_shipping_fees_inr=round(float(agg.shipping or 0), 2),
        total_net_inr=round(float(agg.net or 0), 2),
        pending_count=pending_count,
        processed_count=processed_count,
        duplicate_count=duplicate_count,
        avg_net_refund_inr=round(float(agg.avg_net or 0), 2),
    )


@router.get("/category-returns", response_model=List[schemas.CategoryReturn])
def get_category_returns(db: Session = Depends(get_db)):
    # Count order lines per category
    ol_counts = dict(
        db.query(
            models.OrderLine.category,
            func.count(models.OrderLine.line_id),
        )
        .group_by(models.OrderLine.category)
        .all()
    )

    # Count return lines per category (via order_line join)
    rows = (
        db.query(
            models.OrderLine.category,
            func.count(models.ReturnLine.line_id).label("return_count"),
        )
        .join(models.ReturnLine, models.ReturnLine.order_line_id == models.OrderLine.line_id)
        .group_by(models.OrderLine.category)
        .all()
    )

    # Top reason per category
    top_reason_rows = (
        db.query(
            models.OrderLine.category,
            models.ReturnRequest.reason,
            func.count(models.ReturnLine.line_id).label("cnt"),
        )
        .join(models.ReturnLine, models.ReturnLine.order_line_id == models.OrderLine.line_id)
        .join(models.ReturnRequest, models.ReturnRequest.request_id == models.ReturnLine.request_id)
        .group_by(models.OrderLine.category, models.ReturnRequest.reason)
        .all()
    )

    # Build top-reason map
    top_reason_map: dict = {}
    for r in top_reason_rows:
        cat = r.category.value if hasattr(r.category, "value") else str(r.category)
        reason = r.reason.value if hasattr(r.reason, "value") else str(r.reason)
        if cat not in top_reason_map or r.cnt > top_reason_map[cat][1]:
            top_reason_map[cat] = (reason, r.cnt)

    result = []
    for r in rows:
        cat = r.category.value if hasattr(r.category, "value") else str(r.category)
        total_lines = ol_counts.get(r.category, 1)
        rate = round(r.return_count / total_lines * 100, 2)
        top_r = top_reason_map.get(cat, ("N/A", 0))[0]
        result.append(schemas.CategoryReturn(
            category=cat,
            return_count=r.return_count,
            return_rate_pct=rate,
            top_reason=top_r,
        ))
    return result


@router.get("/anomalies", response_model=List[schemas.AnomalyRecordResponse])
def get_anomalies(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    records = db.query(models.AnomalyRecord).offset(skip).limit(limit).all()
    return records


@router.get("/workflow-funnel", response_model=schemas.WorkflowFunnel)
def get_workflow_funnel(db: Session = Depends(get_db)):
    orders = db.query(func.count(models.Order.order_id)).scalar() or 0
    return_requests = db.query(func.count(models.ReturnRequest.request_id)).scalar() or 0
    authorized = db.query(func.count(models.ReturnAuthorization.auth_id)).scalar() or 0
    shipped = db.query(func.count(models.ReturnShipment.shipment_id)).scalar() or 0
    inspected = db.query(func.count(models.Inspection.inspection_id)).scalar() or 0
    refunded = db.query(func.count(models.Refund.refund_id)).filter(
        models.Refund.status == models.RefundStatus.processed
    ).scalar() or 0
    disposed = db.query(func.count(models.InventoryDisposition.disposition_id)).scalar() or 0

    return schemas.WorkflowFunnel(
        orders=orders,
        return_requests=return_requests,
        authorized=authorized,
        shipped=shipped,
        inspected=inspected,
        refunded=refunded,
        disposed=disposed,
    )
