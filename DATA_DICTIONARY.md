# Data Dictionary — Returns Management System (RMS)

> Version: 1.0 | Seed: 20261022 | Currency: INR | Generated: 2026-10

---

## Table of Contents

1. [Customer](#1-customer)
2. [Order](#2-order)
3. [OrderLine](#3-orderline)
4. [ReturnRequest](#4-returnrequest)
5. [ReturnLine](#5-returnline)
6. [ReturnAuthorization](#6-returnauthorization)
7. [ReturnShipment](#7-returnshipment)
8. [Inspection](#8-inspection)
9. [Refund](#9-refund)
10. [InventoryDisposition](#10-inventorydisposition)
11. [StateTransitionLog](#11-statetransitionlog)
12. [AnomalyRecord](#12-anomalyrecord)

---

## 1. Customer

**Table name:** `customers`  
**CSV file:** `data/customers.csv`  
**Row count:** ~2 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `customer_id` | UUID string | ✅ | UUID v4 format | — | ✅ PK | Must be valid UUID |
| `name` | string | ✅ | 2–100 chars | — | ❌ | Non-empty |
| `email` | string | ✅ | Valid email format | — | ✅ | RFC 5321 format |
| `phone` | string | ✅ | 10-digit Indian mobile | — | ❌ | Matches `[6-9]\d{9}` |
| `address` | string | ✅ | 10–200 chars | — | ❌ | Non-empty |
| `city` | string | ✅ | Indian city name | — | ❌ | From approved cities list |
| `state` | string | ✅ | Indian state name | — | ❌ | Valid Indian state |
| `tier` | enum | ✅ | `standard`, `premium`, `vip` | — | ❌ | One of three values |
| `created_at` | datetime | ✅ | ISO 8601 | UTC | ❌ | ≤ today |
| `is_active` | boolean | ✅ | `true`, `false` | — | ❌ | Default: `true` |

---

## 2. Order

**Table name:** `orders`  
**CSV file:** `data/orders.csv`  
**Row count:** 30 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `order_id` | string | ✅ | `ORD-YYYY-NNNNNN` | — | ✅ PK | Matches pattern |
| `customer_id` | UUID string | ✅ | Valid customer UUID | — | ❌ | FK → customers.customer_id |
| `order_date` | datetime | ✅ | 2026-01-01 to 2026-10-31 | UTC | ❌ | ≤ delivery_date |
| `total_amount_inr` | float | ✅ | > 0 | INR | ❌ | > 0 |
| `discount_amount_inr` | float | ✅ | ≥ 0 | INR | ❌ | ≤ total_amount_inr |
| `tax_amount_inr` | float | ✅ | ≥ 0 | INR | ❌ | ≤ total_amount_inr |
| `net_amount_inr` | float | ✅ | > 0 | INR | ❌ | = total - discount + tax |
| `status` | enum | ✅ | `pending`, `confirmed`, `shipped`, `delivered`, `cancelled` | — | ❌ | One of five values |
| `payment_method` | enum | ✅ | `upi`, `credit_card`, `debit_card`, `net_banking`, `cod`, `emi` | — | ❌ | One of six values |
| `delivery_date` | date | ❌ | ≥ order_date | — | ❌ | Null if not yet delivered |

---

## 3. OrderLine

**Table name:** `order_lines`  
**CSV file:** `data/order_lines.csv`  
**Row count:** ~65 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `line_id` | UUID string | ✅ | UUID v4 | — | ✅ PK | Valid UUID |
| `order_id` | string | ✅ | Valid ORD- pattern | — | ❌ | FK → orders.order_id |
| `product_id` | string | ✅ | `PROD-NNNNNN` | — | ❌ | Matches pattern |
| `product_name` | string | ✅ | 3–100 chars | — | ❌ | Non-empty |
| `category` | enum | ✅ | `electronics`, `clothing`, `books`, `home_appliances`, `furniture`, `perishables`, `jewelry`, `sports`, `toys`, `beauty` | — | ❌ | One of ten values |
| `quantity` | int | ✅ | 1–10 | pieces | ❌ | ≥ 1 |
| `unit_price_inr` | float | ✅ | 10 – 500 000 | INR | ❌ | > 0 |
| `discount_pct` | float | ✅ | 0.0 – 70.0 | % | ❌ | 0 ≤ x ≤ 70 |
| `line_total_inr` | float | ✅ | > 0 | INR | ❌ | = qty × price × (1 - disc/100) |
| `is_returnable` | boolean | ✅ | `true`, `false` | — | ❌ | False for perishables |
| `return_window_days` | int | ✅ | 0, 7, 15, 30, 60, 90 | days | ❌ | 0 for perishables |

---

## 4. ReturnRequest

**Table name:** `return_requests`  
**CSV file:** `data/return_requests.csv`  
**Row count:** 5 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `request_id` | string | ✅ | `RMA-YYYY-NNNNNN` | — | ✅ PK | Matches pattern |
| `customer_id` | UUID string | ✅ | Valid customer UUID | — | ❌ | FK → customers.customer_id |
| `order_id` | string | ✅ | Valid ORD- pattern | — | ❌ | FK → orders.order_id |
| `request_date` | datetime | ✅ | ≥ order delivery_date | UTC | ❌ | ≥ delivery_date |
| `reason` | enum | ✅ | `defective`, `wrong_item`, `not_as_described`, `changed_mind`, `damaged_in_transit`, `sizing_issue`, `quality_issue` | — | ❌ | One of seven values |
| `status` | enum | ✅ | `pending`, `approved`, `partially_approved`, `rejected`, `cancelled` | — | ❌ | One of five values |
| `notes` | string | ❌ | 0–500 chars | — | ❌ | Optional free text |
| `override_flag` | boolean | ✅ | `true`, `false` | — | ❌ | Default: `false` |
| `override_reason` | string | ❌ | 0–200 chars | — | ❌ | Required if override_flag=true |
| `days_since_delivery` | int | ✅ | ≥ 0 | days | ❌ | Computed: request_date - delivery_date |

---

## 5. ReturnLine

**Table name:** `return_lines`  
**CSV file:** `data/return_lines.csv`  
**Row count:** 8 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `line_id` | string | ✅ | `RMAL-{request_id}-NN` | — | ✅ PK | Matches pattern |
| `request_id` | string | ✅ | Valid RMA- pattern | — | ❌ | FK → return_requests.request_id |
| `order_line_id` | UUID string | ✅ | Valid UUID | — | ❌ | FK → order_lines.line_id |
| `requested_qty` | int | ✅ | 1 – original qty | pieces | ❌ | ≤ order_lines.quantity |
| `approved_qty` | int | ❌ | 0 – requested_qty | pieces | ❌ | ≤ requested_qty; null if pending |
| `rejection_reason` | string | ❌ | 0–200 chars | — | ❌ | Required if status=rejected |
| `status` | enum | ✅ | `pending`, `approved`, `rejected` | — | ❌ | One of three values |

---

## 6. ReturnAuthorization

**Table name:** `return_authorizations`  
**CSV file:** `data/return_authorizations.csv`  
**Row count:** ~4 500

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `auth_id` | string | ✅ | `AUTH-YYYY-NNNNNN` | — | ✅ PK | Matches pattern |
| `request_id` | string | ✅ | Valid RMA- pattern | — | ✅ | FK → return_requests.request_id (UNIQUE) |
| `authorized_by` | string | ✅ | 3–50 chars (operator name) | — | ❌ | Non-empty |
| `authorized_at` | datetime | ✅ | ≥ request_date | UTC | ❌ | ≥ return_requests.request_date |
| `expiry_date` | date | ✅ | authorized_at + 14 days | — | ❌ | = authorized_at + 14 days |
| `auth_status` | enum | ✅ | `active`, `expired`, `used`, `cancelled` | — | ❌ | One of four values |

---

## 7. ReturnShipment

**Table name:** `return_shipments`  
**CSV file:** `data/return_shipments.csv`  
**Row count:** ~4 200

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `shipment_id` | string | ✅ | `RTS-YYYY-NNNNNN` | — | ✅ PK | Matches pattern |
| `auth_id` | string | ✅ | Valid AUTH- pattern | — | ❌ | FK → return_authorizations.auth_id |
| `carrier` | string | ✅ | `BlueDart`, `Delhivery`, `DTDC`, `FedEx`, `Ekart`, `Xpressbees` | — | ❌ | One of approved carriers |
| `tracking_number` | string | ✅ | Alphanumeric, 10–20 chars | — | ✅ | Globally unique |
| `shipped_at` | datetime | ❌ | ≥ auth.authorized_at | UTC | ❌ | Null if not yet shipped |
| `received_at` | datetime | ❌ | ≥ shipped_at | UTC | ❌ | Null if not yet received |
| `condition_on_arrival` | enum | ❌ | `good`, `damaged`, `partial`, `missing` | — | ❌ | Null if not yet received |
| `status` | enum | ✅ | `pending`, `in_transit`, `received`, `lost` | — | ❌ | One of four values |

---

## 8. Inspection

**Table name:** `inspections`  
**CSV file:** `data/inspections.csv`  
**Row count:** ~4 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `inspection_id` | UUID string | ✅ | UUID v4 | — | ✅ PK | Valid UUID |
| `shipment_id` | string | ✅ | Valid RTS- pattern | — | ✅ | FK → return_shipments.shipment_id (UNIQUE) |
| `inspector_id` | string | ✅ | `INS-NNN` format | — | ❌ | Assigned inspector |
| `inspected_at` | datetime | ✅ | ≥ shipment.received_at | UTC | ❌ | ≥ received_at |
| `overall_condition` | enum | ✅ | `excellent`, `good`, `fair`, `poor`, `unusable` | — | ❌ | One of five values |
| `notes` | string | ❌ | 0–500 chars | — | ❌ | Optional inspector notes |
| `recommended_action` | enum | ✅ | `restock`, `refurbish`, `quarantine`, `scrap` | — | ❌ | One of four values |

---

## 9. Refund

**Table name:** `refunds`  
**CSV file:** `data/refunds.csv`  
**Row count:** ~3 800

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `refund_id` | string | ✅ | `REF-YYYY-NNNNNN` | — | ✅ PK | Matches pattern |
| `request_id` | string | ✅ | Valid RMA- pattern | — | ❌ | FK → return_requests.request_id |
| `inspection_id` | UUID string | ❌ | Valid UUID | — | ✅ | FK → inspections.inspection_id (UNIQUE, nullable) |
| `gross_refund_inr` | float | ✅ | ≥ 0 | INR | ❌ | ≥ 0 |
| `restocking_fee_inr` | float | ✅ | ≥ 0 | INR | ❌ | ≥ 0 |
| `shipping_fee_inr` | float | ✅ | ≥ 0 | INR | ❌ | ≥ 0 |
| `net_refund_inr` | float | ✅ | Any (can be 0) | INR | ❌ | = gross - restock - shipping |
| `status` | enum | ✅ | `pending`, `approved`, `processed`, `rejected`, `duplicate` | — | ❌ | One of five values |
| `processed_at` | datetime | ❌ | ≥ approval date | UTC | ❌ | Null if not yet processed |
| `payment_method` | string | ✅ | Same as original order payment | — | ❌ | Match order.payment_method |
| `is_duplicate` | boolean | ✅ | `true`, `false` | — | ❌ | Default: `false` |
| `duplicate_of_refund_id` | string | ❌ | Valid REF- pattern | — | ❌ | FK → refunds.refund_id (self-ref, nullable) |

---

## 10. InventoryDisposition

**Table name:** `inventory_dispositions`  
**CSV file:** `data/inventory_dispositions.csv`  
**Row count:** ~4 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `disposition_id` | UUID string | ✅ | UUID v4 | — | ✅ PK | Valid UUID |
| `inspection_id` | UUID string | ✅ | Valid UUID | — | ❌ | FK → inspections.inspection_id |
| `product_id` | string | ✅ | `PROD-NNNNNN` | — | ❌ | Valid product ref |
| `product_name` | string | ✅ | 3–100 chars | — | ❌ | Non-empty |
| `quantity` | int | ✅ | ≥ 1 | pieces | ❌ | ≥ 1 |
| `disposition_action` | enum | ✅ | `restock`, `refurbish`, `quarantine`, `scrap` | — | ❌ | Matches inspection.recommended_action |
| `location` | string | ✅ | Warehouse location code | — | ❌ | e.g. `WH-MUM-A3-R12` |
| `disposed_at` | datetime | ✅ | ≥ inspected_at | UTC | ❌ | ≥ inspections.inspected_at |
| `estimated_recovery_inr` | float | ✅ | ≥ 0 | INR | ❌ | 0 for scrap; > 0 for others |
| `notes` | string | ❌ | 0–300 chars | — | ❌ | Optional |

---

## 11. StateTransitionLog

**Table name:** `state_transition_log`  
**CSV file:** `data/state_transition_log.csv`  
**Row count:** ~25 000

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `log_id` | UUID string | ✅ | UUID v4 | — | ✅ PK | Valid UUID |
| `entity_type` | string | ✅ | `ReturnRequest`, `ReturnAuthorization`, `ReturnShipment`, `Inspection`, `Refund` | — | ❌ | One of five values |
| `entity_id` | string | ✅ | Matching entity PK | — | ❌ | FK to respective entity |
| `from_status` | string | ❌ | Valid status for entity_type | — | ❌ | Null for creation events |
| `to_status` | string | ✅ | Valid status for entity_type | — | ❌ | Valid next state |
| `changed_by` | string | ✅ | Actor identifier | — | ❌ | User/system identifier |
| `changed_at` | datetime | ✅ | Chronological | UTC | ❌ | ≥ previous transition |
| `reason` | string | ❌ | 0–200 chars | — | ❌ | Optional reason note |

---

## 12. AnomalyRecord

**Table name:** `anomaly_records`  
**CSV file:** `data/ground_truth.csv`  
**Row count:** ~500

| Field | Type | Required | Allowed Values / Range | Units | Unique | Validation Rule |
|-------|------|----------|------------------------|-------|--------|-----------------|
| `anomaly_id` | UUID string | ✅ | UUID v4 | — | ✅ PK | Valid UUID |
| `entity_type` | string | ✅ | `ReturnRequest`, `Refund`, `ReturnAuthorization`, etc. | — | ❌ | Valid entity type |
| `entity_id` | string | ✅ | Matching entity PK | — | ❌ | Valid entity reference |
| `anomaly_type` | enum | ✅ | `duplicate_refund`, `late_return_no_override`, `perishable_return`, `orphan_authorization`, `over_refund`, `invalid_state_transition` | — | ❌ | One of six values |
| `severity` | enum | ✅ | `low`, `medium`, `high`, `critical` | — | ❌ | One of four values |
| `description` | string | ✅ | 10–500 chars | — | ❌ | Human-readable description |
| `detected_at` | datetime | ✅ | ISO 8601 | UTC | ❌ | At or after entity creation |
| `is_confirmed` | boolean | ✅ | `true`, `false` | — | ❌ | Ground truth label |

---

## Notes

- All monetary values are in **Indian Rupees (INR)**
- All datetime fields use **UTC ISO 8601** format: `2026-01-15T10:30:00Z`
- All date fields use **YYYY-MM-DD** format
- String enums are **lowercase with underscores** in the database
- The dataset is **100% synthetic** — no real customer or transaction data
