from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime, date
from enum import Enum


# ── Enum mirrors ─────────────────────────────────────────────────────────────

class CustomerTierEnum(str, Enum):
    standard = "standard"
    premium = "premium"
    vip = "vip"


class OrderStatusEnum(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentMethodEnum(str, Enum):
    upi = "upi"
    credit_card = "credit_card"
    debit_card = "debit_card"
    net_banking = "net_banking"
    cod = "cod"
    emi = "emi"


class ProductCategoryEnum(str, Enum):
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


class ReturnReasonEnum(str, Enum):
    defective = "defective"
    wrong_item = "wrong_item"
    not_as_described = "not_as_described"
    changed_mind = "changed_mind"
    damaged_in_transit = "damaged_in_transit"
    sizing_issue = "sizing_issue"
    quality_issue = "quality_issue"


class ReturnRequestStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    partially_approved = "partially_approved"
    rejected = "rejected"
    cancelled = "cancelled"


class ReturnLineStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AuthStatusEnum(str, Enum):
    active = "active"
    expired = "expired"
    used = "used"
    cancelled = "cancelled"


class ShipmentStatusEnum(str, Enum):
    pending = "pending"
    in_transit = "in_transit"
    received = "received"
    lost = "lost"


class ConditionOnArrivalEnum(str, Enum):
    good = "good"
    damaged = "damaged"
    partial = "partial"
    missing = "missing"


class OverallConditionEnum(str, Enum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"
    unusable = "unusable"


class RecommendedActionEnum(str, Enum):
    restock = "restock"
    refurbish = "refurbish"
    quarantine = "quarantine"
    scrap = "scrap"


class RefundStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    processed = "processed"
    rejected = "rejected"
    duplicate = "duplicate"


class DispositionActionEnum(str, Enum):
    restock = "restock"
    refurbish = "refurbish"
    quarantine = "quarantine"
    scrap = "scrap"


class AnomalyIssueTypeEnum(str, Enum):
    return_qty_exceeds_purchased = "return_qty_exceeds_purchased"
    refund_exceeds_paid = "refund_exceeds_paid"
    restock_before_inspection = "restock_before_inspection"
    late_return_no_override = "late_return_no_override"
    duplicate_refund = "duplicate_refund"
    missing_shipment = "missing_shipment"


# ── Generic ───────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[Any]


# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    tier: CustomerTierEnum = CustomerTierEnum.standard
    is_active: bool = True


class CustomerCreate(CustomerBase):
    customer_id: str


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    customer_id: str
    created_at: datetime


# ── Order ─────────────────────────────────────────────────────────────────────

class OrderBase(BaseModel):
    customer_id: str
    order_date: datetime
    total_amount_inr: float
    discount_amount_inr: float = 0.0
    tax_amount_inr: float = 0.0
    net_amount_inr: float
    status: OrderStatusEnum = OrderStatusEnum.pending
    payment_method: PaymentMethodEnum
    delivery_date: Optional[datetime] = None


class OrderCreate(OrderBase):
    order_id: str


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)
    order_id: str


# ── OrderLine ─────────────────────────────────────────────────────────────────

class OrderLineBase(BaseModel):
    order_id: str
    product_id: str
    product_name: str
    category: ProductCategoryEnum
    quantity: int
    unit_price_inr: float
    discount_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    line_total_inr: float
    is_returnable: bool = True
    return_window_days: int = 30


class OrderLineCreate(OrderLineBase):
    line_id: str


class OrderLineResponse(OrderLineBase):
    model_config = ConfigDict(from_attributes=True)
    line_id: str


# ── ReturnRequest ─────────────────────────────────────────────────────────────

class ReturnRequestBase(BaseModel):
    customer_id: str
    order_id: str
    request_date: datetime
    reason: ReturnReasonEnum
    status: ReturnRequestStatusEnum = ReturnRequestStatusEnum.pending
    notes: Optional[str] = None
    override_flag: bool = False
    override_reason: Optional[str] = None
    days_since_delivery: int = 0


class ReturnRequestCreate(ReturnRequestBase):
    request_id: str


class ReturnRequestResponse(ReturnRequestBase):
    model_config = ConfigDict(from_attributes=True)
    request_id: str


# ── ReturnLine ────────────────────────────────────────────────────────────────

class ReturnLineBase(BaseModel):
    request_id: str
    order_line_id: str
    requested_qty: int
    approved_qty: Optional[int] = None
    rejection_reason: Optional[str] = None
    status: ReturnLineStatusEnum = ReturnLineStatusEnum.pending


class ReturnLineCreate(ReturnLineBase):
    line_id: str


class ReturnLineResponse(ReturnLineBase):
    model_config = ConfigDict(from_attributes=True)
    line_id: str


# ── ReturnAuthorization ───────────────────────────────────────────────────────

class ReturnAuthorizationBase(BaseModel):
    request_id: str
    authorized_by: str
    authorized_at: datetime
    expiry_date: date
    auth_status: AuthStatusEnum = AuthStatusEnum.active


class ReturnAuthorizationCreate(ReturnAuthorizationBase):
    auth_id: str


class ReturnAuthorizationResponse(ReturnAuthorizationBase):
    model_config = ConfigDict(from_attributes=True)
    auth_id: str


# ── ReturnShipment ────────────────────────────────────────────────────────────

class ReturnShipmentBase(BaseModel):
    auth_id: str
    carrier: str
    tracking_number: str
    shipped_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    condition_on_arrival: Optional[ConditionOnArrivalEnum] = None
    status: ShipmentStatusEnum = ShipmentStatusEnum.pending


class ReturnShipmentCreate(ReturnShipmentBase):
    shipment_id: str


class ReturnShipmentResponse(ReturnShipmentBase):
    model_config = ConfigDict(from_attributes=True)
    shipment_id: str


# ── Inspection ────────────────────────────────────────────────────────────────

class InspectionBase(BaseModel):
    shipment_id: str
    inspector_id: str
    inspected_at: datetime
    overall_condition: OverallConditionEnum
    notes: Optional[str] = None
    recommended_action: RecommendedActionEnum


class InspectionCreate(InspectionBase):
    inspection_id: str


class InspectionResponse(InspectionBase):
    model_config = ConfigDict(from_attributes=True)
    inspection_id: str


# ── Refund ────────────────────────────────────────────────────────────────────

class RefundBase(BaseModel):
    request_id: str
    inspection_id: Optional[str] = None
    gross_refund_inr: float
    restocking_fee_inr: float = 0.0
    shipping_fee_inr: float = 0.0
    net_refund_inr: float
    status: RefundStatusEnum = RefundStatusEnum.pending
    processed_at: Optional[datetime] = None
    payment_method: str
    is_duplicate: bool = False
    duplicate_of_refund_id: Optional[str] = None


class RefundCreate(RefundBase):
    refund_id: str


class RefundResponse(RefundBase):
    model_config = ConfigDict(from_attributes=True)
    refund_id: str


# ── InventoryDisposition ──────────────────────────────────────────────────────

class InventoryDispositionBase(BaseModel):
    inspection_id: str
    product_id: str
    product_name: str
    quantity: int
    action: DispositionActionEnum
    warehouse_location: str
    disposition_date: date
    estimated_recovery_value_inr: float = 0.0
    actual_recovery_value_inr: Optional[float] = None
    notes: Optional[str] = None


class InventoryDispositionCreate(InventoryDispositionBase):
    disposition_id: str


class InventoryDispositionResponse(InventoryDispositionBase):
    model_config = ConfigDict(from_attributes=True)
    disposition_id: str


# ── StateTransitionLog ────────────────────────────────────────────────────────

class StateTransitionLogBase(BaseModel):
    entity_type: str
    entity_id: str
    from_status: Optional[str] = None
    to_status: str
    changed_by: str
    changed_at: datetime
    reason: Optional[str] = None


class StateTransitionLogCreate(StateTransitionLogBase):
    log_id: str


class StateTransitionLogResponse(StateTransitionLogBase):
    model_config = ConfigDict(from_attributes=True)
    log_id: str


# ── AnomalyRecord ─────────────────────────────────────────────────────────────

class AnomalyRecordBase(BaseModel):
    entity_type: str
    entity_id: str
    issue_type: AnomalyIssueTypeEnum
    ground_truth_label: bool = True
    detected_at: datetime
    details_json: Optional[str] = None


class AnomalyRecordCreate(AnomalyRecordBase):
    anomaly_id: str


class AnomalyRecordResponse(AnomalyRecordBase):
    model_config = ConfigDict(from_attributes=True)
    anomaly_id: str


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardOverview(BaseModel):
    total_orders: int
    total_return_requests: int
    return_rate_pct: float
    avg_refund_amount_inr: float
    pending_approvals: int
    total_refunded_inr: float
    total_refunded_this_month_inr: float
    anomaly_count: int


class ReturnTrend(BaseModel):
    date: str
    return_count: int
    approval_count: int


class DispositionBreakdown(BaseModel):
    action: str
    count: int
    estimated_recovery_inr: float


class CategoryReturn(BaseModel):
    category: str
    return_count: int
    return_rate_pct: float
    top_reason: str


class WorkflowFunnel(BaseModel):
    orders: int
    return_requests: int
    authorized: int
    shipped: int
    inspected: int
    refunded: int
    disposed: int


class TopReturnReason(BaseModel):
    reason: str
    count: int
    percentage: float


class RefundSummary(BaseModel):
    total_gross_inr: float
    total_restocking_fees_inr: float
    total_shipping_fees_inr: float
    total_net_inr: float
    pending_count: int
    processed_count: int
    duplicate_count: int
    avg_net_refund_inr: float
