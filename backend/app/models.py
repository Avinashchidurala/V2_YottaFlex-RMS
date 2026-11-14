from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Text,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class CustomerTier(str, enum.Enum):
    standard = "standard"
    premium = "premium"
    vip = "vip"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentMethod(str, enum.Enum):
    upi = "upi"
    credit_card = "credit_card"
    debit_card = "debit_card"
    net_banking = "net_banking"
    cod = "cod"
    emi = "emi"


class ProductCategory(str, enum.Enum):
    electronics = "electronics"
    clothing = "clothing"
    books = "books"
    home_appliances = "home_appliances"
    furniture = "furniture"
    perishables = "perishables"
    jewelry = "jewelry"
    sports = "sports"
    toys = "toys"
    beauty = "beauty"


class ReturnReason(str, enum.Enum):
    defective = "defective"
    wrong_item = "wrong_item"
    not_as_described = "not_as_described"
    changed_mind = "changed_mind"
    damaged_in_transit = "damaged_in_transit"
    sizing_issue = "sizing_issue"
    quality_issue = "quality_issue"


class ReturnRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    partially_approved = "partially_approved"
    rejected = "rejected"
    cancelled = "cancelled"


class ReturnLineStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AuthStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    used = "used"
    cancelled = "cancelled"


class ShipmentStatus(str, enum.Enum):
    pending = "pending"
    in_transit = "in_transit"
    received = "received"
    lost = "lost"


class ConditionOnArrival(str, enum.Enum):
    good = "good"
    damaged = "damaged"
    partial = "partial"
    missing = "missing"


class OverallCondition(str, enum.Enum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"
    unusable = "unusable"


class RecommendedAction(str, enum.Enum):
    restock = "restock"
    refurbish = "refurbish"
    quarantine = "quarantine"
    scrap = "scrap"


class RefundStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    processed = "processed"
    rejected = "rejected"
    duplicate = "duplicate"


class DispositionAction(str, enum.Enum):
    restock = "restock"
    refurbish = "refurbish"
    quarantine = "quarantine"
    scrap = "scrap"


class AnomalyIssueType(str, enum.Enum):
    return_qty_exceeds_purchased = "return_qty_exceeds_purchased"
    refund_exceeds_paid = "refund_exceeds_paid"
    restock_before_inspection = "restock_before_inspection"
    late_return_no_override = "late_return_no_override"
    duplicate_refund = "duplicate_refund"
    missing_shipment = "missing_shipment"


# ── Models ───────────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    tier = Column(SAEnum(CustomerTier), nullable=False, default=CustomerTier.standard)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    orders = relationship("Order", back_populates="customer")
    return_requests = relationship("ReturnRequest", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)  # e.g. ORD-2026-000001
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    order_date = Column(DateTime, nullable=False)
    total_amount_inr = Column(Float, nullable=False)
    discount_amount_inr = Column(Float, nullable=False, default=0.0)
    tax_amount_inr = Column(Float, nullable=False, default=0.0)
    net_amount_inr = Column(Float, nullable=False)
    status = Column(SAEnum(OrderStatus), nullable=False, default=OrderStatus.pending)
    payment_method = Column(SAEnum(PaymentMethod), nullable=False)
    delivery_date = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="orders")
    order_lines = relationship("OrderLine", back_populates="order")
    return_requests = relationship("ReturnRequest", back_populates="order")


class OrderLine(Base):
    __tablename__ = "order_lines"

    line_id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False, index=True)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    category = Column(SAEnum(ProductCategory), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_inr = Column(Float, nullable=False)
    discount_pct = Column(Float, nullable=False, default=0.0)
    line_total_inr = Column(Float, nullable=False)
    is_returnable = Column(Boolean, nullable=False, default=True)
    return_window_days = Column(Integer, nullable=False, default=30)

    order = relationship("Order", back_populates="order_lines")
    return_lines = relationship("ReturnLine", back_populates="order_line")


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    request_id = Column(String, primary_key=True, index=True)  # e.g. RMA-2026-000001
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False, index=True)
    request_date = Column(DateTime, nullable=False, default=func.now())
    reason = Column(SAEnum(ReturnReason), nullable=False)
    status = Column(SAEnum(ReturnRequestStatus), nullable=False, default=ReturnRequestStatus.pending)
    notes = Column(Text, nullable=True)
    override_flag = Column(Boolean, nullable=False, default=False)
    override_reason = Column(Text, nullable=True)
    days_since_delivery = Column(Integer, nullable=False, default=0)

    customer = relationship("Customer", back_populates="return_requests")
    order = relationship("Order", back_populates="return_requests")
    return_lines = relationship("ReturnLine", back_populates="return_request")
    authorization = relationship("ReturnAuthorization", back_populates="return_request", uselist=False)
    refunds = relationship("Refund", back_populates="return_request")


class ReturnLine(Base):
    __tablename__ = "return_lines"

    line_id = Column(String, primary_key=True, index=True)  # e.g. RMAL-RMA-2026-000001-01
    request_id = Column(String, ForeignKey("return_requests.request_id"), nullable=False, index=True)
    order_line_id = Column(String, ForeignKey("order_lines.line_id"), nullable=False, index=True)
    requested_qty = Column(Integer, nullable=False)
    approved_qty = Column(Integer, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    status = Column(SAEnum(ReturnLineStatus), nullable=False, default=ReturnLineStatus.pending)

    return_request = relationship("ReturnRequest", back_populates="return_lines")
    order_line = relationship("OrderLine", back_populates="return_lines")


class ReturnAuthorization(Base):
    __tablename__ = "return_authorizations"

    auth_id = Column(String, primary_key=True, index=True)
    request_id = Column(String, ForeignKey("return_requests.request_id"), unique=True, nullable=False, index=True)
    authorized_by = Column(String, nullable=False)
    authorized_at = Column(DateTime, nullable=False, default=func.now())
    expiry_date = Column(Date, nullable=False)
    auth_status = Column(SAEnum(AuthStatus), nullable=False, default=AuthStatus.active)

    return_request = relationship("ReturnRequest", back_populates="authorization")
    shipments = relationship("ReturnShipment", back_populates="authorization")


class ReturnShipment(Base):
    __tablename__ = "return_shipments"

    shipment_id = Column(String, primary_key=True, index=True)  # e.g. RTS-2026-000001
    auth_id = Column(String, ForeignKey("return_authorizations.auth_id"), nullable=False, index=True)
    carrier = Column(String, nullable=False)
    tracking_number = Column(String, nullable=False)
    shipped_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    condition_on_arrival = Column(SAEnum(ConditionOnArrival), nullable=True)
    status = Column(SAEnum(ShipmentStatus), nullable=False, default=ShipmentStatus.pending)

    authorization = relationship("ReturnAuthorization", back_populates="shipments")
    inspection = relationship("Inspection", back_populates="shipment", uselist=False)


class Inspection(Base):
    __tablename__ = "inspections"

    inspection_id = Column(String, primary_key=True, index=True)
    shipment_id = Column(String, ForeignKey("return_shipments.shipment_id"), unique=True, nullable=False, index=True)
    inspector_id = Column(String, nullable=False)
    inspected_at = Column(DateTime, nullable=False, default=func.now())
    overall_condition = Column(SAEnum(OverallCondition), nullable=False)
    notes = Column(Text, nullable=True)
    recommended_action = Column(SAEnum(RecommendedAction), nullable=False)

    shipment = relationship("ReturnShipment", back_populates="inspection")
    refund = relationship("Refund", back_populates="inspection", uselist=False)
    dispositions = relationship("InventoryDisposition", back_populates="inspection")


class Refund(Base):
    __tablename__ = "refunds"

    refund_id = Column(String, primary_key=True, index=True)  # e.g. REF-2026-000001
    request_id = Column(String, ForeignKey("return_requests.request_id"), nullable=False, index=True)
    inspection_id = Column(String, ForeignKey("inspections.inspection_id"), unique=True, nullable=True, index=True)
    gross_refund_inr = Column(Float, nullable=False)
    restocking_fee_inr = Column(Float, nullable=False, default=0.0)
    shipping_fee_inr = Column(Float, nullable=False, default=0.0)
    net_refund_inr = Column(Float, nullable=False)
    status = Column(SAEnum(RefundStatus), nullable=False, default=RefundStatus.pending)
    processed_at = Column(DateTime, nullable=True)
    payment_method = Column(String, nullable=False)
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_of_refund_id = Column(String, nullable=True)

    return_request = relationship("ReturnRequest", back_populates="refunds")
    inspection = relationship("Inspection", back_populates="refund")


class InventoryDisposition(Base):
    __tablename__ = "inventory_dispositions"

    disposition_id = Column(String, primary_key=True, index=True)
    inspection_id = Column(String, ForeignKey("inspections.inspection_id"), nullable=False, index=True)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    action = Column(SAEnum(DispositionAction), nullable=False)
    warehouse_location = Column(String, nullable=False)
    disposition_date = Column(Date, nullable=False)
    estimated_recovery_value_inr = Column(Float, nullable=False, default=0.0)
    actual_recovery_value_inr = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    inspection = relationship("Inspection", back_populates="dispositions")


class StateTransitionLog(Base):
    __tablename__ = "state_transition_logs"

    log_id = Column(String, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    changed_by = Column(String, nullable=False)
    changed_at = Column(DateTime, nullable=False, default=func.now())
    reason = Column(Text, nullable=True)


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    anomaly_id = Column(String, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    issue_type = Column(SAEnum(AnomalyIssueType), nullable=False)
    ground_truth_label = Column(Boolean, nullable=False, default=True)
    detected_at = Column(DateTime, nullable=False, default=func.now())
    details_json = Column(Text, nullable=True)
