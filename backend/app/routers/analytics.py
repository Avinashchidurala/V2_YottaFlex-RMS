from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/analytics")


@router.get("/return-eligibility-decisions")
def return_eligibility_decisions(db: Session = Depends(get_db)):
    """
    Summarises eligibility outcomes:
    - eligible: delivered orders where at least one order line is returnable
      and return_window_days > 0
    - ineligible_window_closed: delivered orders where delivery_date is set and
      the maximum return window has passed for all lines
    - ineligible_non_returnable: orders with no returnable lines
    - return_requested: orders that actually have a return request
    - override_approved: late returns approved with override_flag
    """
    total_delivered = db.query(func.count(models.Order.order_id)).filter(
        models.Order.status == models.OrderStatus.delivered
    ).scalar() or 0

    eligible = (
        db.query(func.count(func.distinct(models.OrderLine.order_id)))
        .filter(
            models.OrderLine.is_returnable == True,
            models.OrderLine.return_window_days > 0,
        )
        .scalar() or 0
    )

    non_returnable_orders = (
        db.query(func.count(func.distinct(models.OrderLine.order_id)))
        .filter(models.OrderLine.is_returnable == False)
        .scalar() or 0
    )

    return_requested = db.query(func.count(func.distinct(models.ReturnRequest.order_id))).scalar() or 0

    override_approved = db.query(func.count(models.ReturnRequest.request_id)).filter(
        models.ReturnRequest.override_flag == True,
        models.ReturnRequest.status == models.ReturnRequestStatus.approved,
    ).scalar() or 0

    late_return_anomalies = db.query(func.count(models.AnomalyRecord.anomaly_id)).filter(
        models.AnomalyRecord.issue_type == models.AnomalyIssueType.late_return_no_override
    ).scalar() or 0

    return {
        "total_delivered_orders": total_delivered,
        "eligible_for_return": eligible,
        "non_returnable_product_orders": non_returnable_orders,
        "return_requested": return_requested,
        "override_approved_late_returns": override_approved,
        "late_return_anomalies": late_return_anomalies,
        "return_conversion_rate_pct": round(return_requested / eligible * 100, 2) if eligible > 0 else 0.0,
    }


@router.get("/refund-reconciliation")
def refund_reconciliation(db: Session = Depends(get_db)):
    """
    Reconciles refunds against original order amounts:
    - Total paid by customers (net_amount_inr of orders with return requests)
    - Total gross refunds issued
    - Total net refunds processed
    - Overpayments (net_refund > original order net_amount)
    - Avg refund percentage of order value
    """
    # Orders that have at least one processed refund
    refunded_orders = (
        db.query(models.Order.net_amount_inr, models.Refund.gross_refund_inr, models.Refund.net_refund_inr)
        .join(models.ReturnRequest, models.ReturnRequest.order_id == models.Order.order_id)
        .join(models.Refund, models.Refund.request_id == models.ReturnRequest.request_id)
        .filter(models.Refund.status == models.RefundStatus.processed)
        .all()
    )

    total_order_value = sum(r.net_amount_inr for r in refunded_orders)
    total_gross_refund = sum(r.gross_refund_inr for r in refunded_orders)
    total_net_refund = sum(r.net_refund_inr for r in refunded_orders)
    overpayments = sum(1 for r in refunded_orders if r.net_refund_inr > r.net_amount_inr)

    avg_refund_pct = (
        round(total_net_refund / total_order_value * 100, 2) if total_order_value > 0 else 0.0
    )

    duplicate_refunds = db.query(func.count(models.Refund.refund_id)).filter(
        models.Refund.is_duplicate == True
    ).scalar() or 0

    refund_exceeds_paid_anomalies = db.query(func.count(models.AnomalyRecord.anomaly_id)).filter(
        models.AnomalyRecord.issue_type == models.AnomalyIssueType.refund_exceeds_paid
    ).scalar() or 0

    return {
        "processed_refund_count": len(refunded_orders),
        "total_order_value_for_refunded_orders_inr": round(total_order_value, 2),
        "total_gross_refunded_inr": round(total_gross_refund, 2),
        "total_net_refunded_inr": round(total_net_refund, 2),
        "avg_refund_pct_of_order_value": avg_refund_pct,
        "overpayment_cases": overpayments,
        "duplicate_refund_count": duplicate_refunds,
        "refund_exceeds_paid_anomalies": refund_exceeds_paid_anomalies,
    }


@router.get("/anomaly-report")
def anomaly_report(
    issue_type: Optional[str] = None,
    ground_truth: Optional[bool] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Ground-truth anomaly report. Returns all anomaly records with counts per type.
    Supports filtering by issue_type and ground_truth_label.
    """
    q = db.query(models.AnomalyRecord)
    if issue_type:
        q = q.filter(models.AnomalyRecord.issue_type == issue_type)
    if ground_truth is not None:
        q = q.filter(models.AnomalyRecord.ground_truth_label == ground_truth)

    total = q.count()
    records = q.order_by(models.AnomalyRecord.detected_at.desc()).offset(skip).limit(limit).all()

    # Summary by type
    type_summary = (
        db.query(
            models.AnomalyRecord.issue_type,
            func.count(models.AnomalyRecord.anomaly_id).label("count"),
            func.sum(
                func.case((models.AnomalyRecord.ground_truth_label == True, 1), else_=0)
            ).label("true_positives"),
        )
        .group_by(models.AnomalyRecord.issue_type)
        .all()
    )

    summary = [
        {
            "issue_type": r.issue_type.value if hasattr(r.issue_type, "value") else str(r.issue_type),
            "total_count": r.count,
            "true_positives": int(r.true_positives or 0),
            "false_positives": int(r.count - (r.true_positives or 0)),
        }
        for r in type_summary
    ]

    return {
        "total_anomalies": total,
        "summary_by_type": summary,
        "records": [schemas.AnomalyRecordResponse.model_validate(rec) for rec in records],
    }
