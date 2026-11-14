# Schema — Returns Management System (RMS)

> Version: 1.0 | Database: SQLite (`data/rms.db`) | ORM: SQLAlchemy

---

## Table of Contents

1. [Entity Overview](#1-entity-overview)
2. [ER Diagram](#2-er-diagram)
3. [Cardinality & Foreign Keys](#3-cardinality--foreign-keys)
4. [Entity Field Listings](#4-entity-field-listings)
5. [Lifecycle State Machines](#5-lifecycle-state-machines)
6. [Bridge / Audit Tables](#6-bridge--audit-tables)

---

## 1. Entity Overview

| Entity | Table Name | PK Format | Row Count | Purpose |
|---|---|---|---|---|
| Customer | `customers` | `CUST-IND-NNN` | 3 | Core customer profiles for panel |
| Inventory | `inventory` | `PROD-CAT-NNN` | 14 | Catalog products with stock & pricing |
| Order | `orders` | `ORD-2026-NNNNNN` | 30 000 | Purchase transactions |
| OrderLine | `order_lines` | `LINE-ORD-2026-...` | 54 163 | Individual items per order |
| ReturnRequest | `return_requests` | `RMA-2026-NNNNNN` | 5 000 | Return initiation |
| ReturnLine | `return_lines` | `RMAL-RMA-2026-...` | 8 000 | Exactly 8,000 return lines |
| ReturnAuthorization | `return_authorizations` | `AUTH-2026-NNNNNN` | 3 352 | Issued return approval |
| ReturnShipment | `return_shipments` | `RTS-2026-NNNNNN` | 3 352 | Physical return transit |
| Inspection | `inspections` | `INSP-2026-NNNNNN` | 3 332 | Warehouse quality check |
| Refund | `refunds` | `REF-2026-NNNNNN` | 4 117 | Financial reimbursement |
| InventoryDisposition | `inventory_dispositions` | `DISP-2026-NNNNNN` | 4 082 | Item fate post-inspection |
| StateTransitionLog | `state_transition_log` | `LOG-2026-NNNNNN` | 750 | Audit trail |
| AnomalyRecord | `anomaly_records` | `ANOM-2026-NNNNNN` | 200 | Ground truth anomalies |

---

## 2. ER Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ENTITY RELATIONSHIP DIAGRAM                        │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────┐         ┌─────────────┐         ┌─────────────────┐
│  Customer   │ 1     N │   Order     │ 1     N │   OrderLine     │
│ ─────────── │────────►│ ─────────── │────────►│ ─────────────── │
│ customer_id │         │ order_id    │         │ line_id (UUID)  │
│ name        │         │ customer_id │         │ order_id        │
│ email       │         │ order_date  │         │ product_id      │
│ phone       │         │ status      │         │ category        │
│ city        │         │ payment_met │         │ quantity        │
│ state       │         │ net_amount  │         │ unit_price_inr  │
│ tier        │         │ delivery_dt │         │ return_window   │
└─────────────┘         └──────┬──────┘         └────────┬────────┘
                               │ 1                       │
                               │ N                       │ N
                               ▼                         │
                  ┌────────────────────┐                 │
                  │  ReturnRequest     │                 │
                  │ ────────────────── │                 │
                  │ request_id (RMA-)  │◄────────────────┘
                  │ customer_id        │         (via ReturnLine)
                  │ order_id           │
                  │ request_date       │
                  │ reason             │
                  │ status             │
                  │ override_flag      │
                  │ days_since_deliv   │
                  └────────┬───────────┘
                           │ 1:N (order has N return requests)
                           │ 1:N (request has N return lines)
                           │
                           │ 1
                           │
              ┌────────────┼──────────────────────┐
              │            │                      │
              ▼            ▼                      ▼
    ┌──────────────┐ ┌───────────┐    ┌────────────────────────┐
    │ ReturnLine   │ │ Refund    │    │  ReturnAuthorization    │
    │ ──────────── │ │ ───────── │    │ ─────────────────────── │
    │ RMAL-...-NN  │ │ REF-NNNN  │    │ auth_id (AUTH-)         │
    │ request_id   │ │ request_id│    │ request_id (FK, UNIQUE) │
    │ order_line_id│ │ inspect_id│    │ authorized_by           │
    │ requested_qty│ │ gross_ref │    │ authorized_at           │
    │ approved_qty │ │ restock_fe│    │ expiry_date             │
    │ status       │ │ ship_fee  │    │ auth_status             │
    └──────────────┘ │ net_refund│    └──────────┬─────────────┘
                     │ is_dup    │               │ 1
                     └───────────┘               │
                          ▲                      ▼
                          │ 1              ┌──────────────────┐
                          │               │  ReturnShipment  │
                 ┌────────┴───────┐       │ ──────────────── │
                 │  Inspection    │       │ shipment_id(RTS-)│
                 │ ─────────────  │       │ auth_id (FK)     │
                 │ inspection_id  │◄──────│ carrier          │
                 │ shipment_id FK │ 1:1   │ tracking_number  │
                 │ overall_cond   │       │ shipped_at       │
                 │ recommended_ac │       │ received_at      │
                 └───────┬────────┘       │ status           │
                         │               └──────────────────┘
                         │ 1:N
                         ▼
              ┌────────────────────────┐
              │  InventoryDisposition  │
              │ ────────────────────── │
              │ disposition_id (UUID)  │
              │ inspection_id (FK)     │
              │ product_id             │
              │ disposition_action     │
              │ location               │
              │ estimated_recovery_inr │
              └────────────────────────┘

Audit / Support tables:
  StateTransitionLog → references any entity by (entity_type, entity_id)
  AnomalyRecord      → references any entity by (entity_type, entity_id)
```

---

## 3. Cardinality & Foreign Keys

### Cardinality

| Relationship | Type | Note |
|---|---|---|
| Customer → Orders | 1 : N | One customer, many orders |
| Order → OrderLines | 1 : N | One order, 1–5 lines |
| Order → ReturnRequests | 1 : N | An order can have multiple partial returns |
| Customer → ReturnRequests | 1 : N | Via customer_id on return_request |
| ReturnRequest → ReturnLines | 1 : N | 1–3 lines per return request |
| ReturnLine → OrderLine | N : 1 | Line references originating order line |
| ReturnRequest → ReturnAuthorization | 1 : 0..1 | At most one auth per request |
| ReturnAuthorization → ReturnShipment | 1 : 0..1 | At most one shipment per auth |
| ReturnShipment → Inspection | 1 : 0..1 | At most one inspection per shipment |
| Inspection → Refund | 1 : 0..1 | At most one primary refund per inspection |
| ReturnRequest → Refunds | 1 : N | Duplicate refunds share same request_id |
| Inspection → InventoryDispositions | 1 : N | Typically 1; can be multiple for multi-item |
| Any entity → StateTransitionLog | 1 : N | Audit entries per status change |
| Any entity → AnomalyRecord | 1 : N | Multiple anomaly types per entity |

### Foreign Key Reference Table

| Table | Column | References |
|---|---|---|
| `orders` | `customer_id` | `customers.customer_id` |
| `order_lines` | `order_id` | `orders.order_id` |
| `return_requests` | `customer_id` | `customers.customer_id` |
| `return_requests` | `order_id` | `orders.order_id` |
| `return_lines` | `request_id` | `return_requests.request_id` |
| `return_lines` | `order_line_id` | `order_lines.line_id` |
| `return_authorizations` | `request_id` | `return_requests.request_id` (UNIQUE) |
| `return_shipments` | `auth_id` | `return_authorizations.auth_id` |
| `inspections` | `shipment_id` | `return_shipments.shipment_id` (UNIQUE) |
| `refunds` | `request_id` | `return_requests.request_id` |
| `refunds` | `inspection_id` | `inspections.inspection_id` (UNIQUE, nullable) |
| `refunds` | `duplicate_of_refund_id` | `refunds.refund_id` (self-ref, nullable) |
| `inventory_dispositions` | `inspection_id` | `inspections.inspection_id` |

---

## 4. Entity Field Listings

### Customer
```
customer_id      TEXT  PK
name             TEXT
email            TEXT  UNIQUE
phone            TEXT
address          TEXT
city             TEXT
state            TEXT
tier             TEXT  CHECK(tier IN ('standard','premium','vip'))
created_at       TEXT  (ISO 8601 datetime)
is_active        INTEGER (0/1)
```

### Order
```
order_id              TEXT  PK  (ORD-YYYY-NNNNNN)
customer_id           TEXT  FK → customers
order_date            TEXT  (ISO 8601 datetime)
total_amount_inr      REAL
discount_amount_inr   REAL
tax_amount_inr        REAL
net_amount_inr        REAL
status                TEXT  CHECK(status IN ('pending','confirmed','shipped','delivered','cancelled'))
payment_method        TEXT  CHECK(method IN ('upi','credit_card','debit_card','net_banking','cod','emi'))
delivery_date         TEXT  (DATE, nullable)
```

### OrderLine
```
line_id              TEXT  PK  (UUID)
order_id             TEXT  FK → orders
product_id           TEXT
product_name         TEXT
category             TEXT  CHECK(category IN ('electronics','clothing','books','home_appliances',
                            'furniture','perishables','jewelry','sports','toys','beauty'))
quantity             INTEGER
unit_price_inr       REAL
discount_pct         REAL  (0-70)
line_total_inr       REAL
is_returnable        INTEGER (0/1)
return_window_days   INTEGER (0,7,15,30,60,90)
```

### ReturnRequest
```
request_id           TEXT  PK  (RMA-YYYY-NNNNNN)
customer_id          TEXT  FK → customers
order_id             TEXT  FK → orders
request_date         TEXT  (ISO 8601 datetime)
reason               TEXT  CHECK(reason IN ('defective','wrong_item','not_as_described',
                            'changed_mind','damaged_in_transit','sizing_issue','quality_issue'))
status               TEXT  CHECK(status IN ('pending','approved','partially_approved','rejected','cancelled'))
notes                TEXT  nullable
override_flag        INTEGER (0/1)
override_reason      TEXT  nullable
days_since_delivery  INTEGER
```

### ReturnLine
```
line_id              TEXT  PK  (RMAL-{request_id}-NN)
request_id           TEXT  FK → return_requests
order_line_id        TEXT  FK → order_lines
requested_qty        INTEGER
approved_qty         INTEGER nullable
rejection_reason     TEXT  nullable
status               TEXT  CHECK(status IN ('pending','approved','rejected'))
```

### ReturnAuthorization
```
auth_id              TEXT  PK  (AUTH-YYYY-NNNNNN)
request_id           TEXT  FK → return_requests  UNIQUE
authorized_by        TEXT
authorized_at        TEXT  (ISO 8601 datetime)
expiry_date          TEXT  (DATE)
auth_status          TEXT  CHECK(status IN ('active','expired','used','cancelled'))
```

### ReturnShipment
```
shipment_id          TEXT  PK  (RTS-YYYY-NNNNNN)
auth_id              TEXT  FK → return_authorizations
carrier              TEXT
tracking_number      TEXT  UNIQUE
shipped_at           TEXT  nullable
received_at          TEXT  nullable
condition_on_arrival TEXT  nullable CHECK(condition IN ('good','damaged','partial','missing'))
status               TEXT  CHECK(status IN ('pending','in_transit','received','lost'))
```

### Inspection
```
inspection_id        TEXT  PK  (UUID)
shipment_id          TEXT  FK → return_shipments  UNIQUE
inspector_id         TEXT
inspected_at         TEXT  (ISO 8601 datetime)
overall_condition    TEXT  CHECK(condition IN ('excellent','good','fair','poor','unusable'))
notes                TEXT  nullable
recommended_action   TEXT  CHECK(action IN ('restock','refurbish','quarantine','scrap'))
```

### Refund
```
refund_id                TEXT  PK  (REF-YYYY-NNNNNN)
request_id               TEXT  FK → return_requests
inspection_id            TEXT  FK → inspections  UNIQUE nullable
gross_refund_inr         REAL
restocking_fee_inr       REAL  DEFAULT 0
shipping_fee_inr         REAL  DEFAULT 0
net_refund_inr           REAL
status                   TEXT  CHECK(status IN ('pending','approved','processed','rejected','duplicate'))
processed_at             TEXT  nullable
payment_method           TEXT
is_duplicate             INTEGER (0/1) DEFAULT 0
duplicate_of_refund_id   TEXT  FK → refunds (self-ref) nullable
```

### InventoryDisposition
```
disposition_id           TEXT  PK  (UUID)
inspection_id            TEXT  FK → inspections
product_id               TEXT
product_name             TEXT
quantity                 INTEGER
disposition_action       TEXT  CHECK(action IN ('restock','refurbish','quarantine','scrap'))
location                 TEXT
disposed_at              TEXT  (ISO 8601 datetime)
estimated_recovery_inr   REAL
notes                    TEXT  nullable
```

### StateTransitionLog
```
log_id               TEXT  PK  (UUID)
entity_type          TEXT  CHECK(type IN ('ReturnRequest','ReturnAuthorization',
                            'ReturnShipment','Inspection','Refund'))
entity_id            TEXT
from_status          TEXT  nullable
to_status            TEXT
changed_by           TEXT
changed_at           TEXT  (ISO 8601 datetime)
reason               TEXT  nullable
```

### AnomalyRecord
```
anomaly_id           TEXT  PK  (UUID)
entity_type          TEXT
entity_id            TEXT
anomaly_type         TEXT  CHECK(type IN ('duplicate_refund','late_return_no_override',
                            'perishable_return','orphan_authorization',
                            'over_refund','invalid_state_transition'))
severity             TEXT  CHECK(severity IN ('low','medium','high','critical'))
description          TEXT
detected_at          TEXT  (ISO 8601 datetime)
is_confirmed         INTEGER (0/1)
```

---

## 5. Lifecycle State Machines

### ReturnRequest Status

```
                    ┌──────────┐
         submit     │          │
  ───────────────►  │ pending  │
                    │          │
                    └────┬─────┘
                         │
              ┌──────────┼──────────────────┐
              │          │                  │
           approve    partially           reject
              │        approve              │
              ▼          │                  ▼
         ┌─────────┐     │          ┌────────────┐
         │approved │     │          │  rejected  │
         └─────────┘     │          └────────────┘
                         ▼
              ┌──────────────────┐
              │partially_approved│
              └──────────────────┘

  Any state ──cancel──► cancelled
```

### ReturnAuthorization Status

```
  ┌────────┐              ┌─────────┐
  │ active │──14 days──►  │ expired │
  └───┬────┘              └─────────┘
      │
      │ shipment created
      ▼
  ┌──────┐
  │ used │
  └──────┘
  
  active ──manager action──► cancelled
```

### ReturnShipment Status

```
  ┌─────────┐           ┌────────────┐           ┌──────────┐
  │ pending │ ──ship──► │ in_transit │ ──arrive──►│ received │
  └─────────┘           └──────┬─────┘           └──────────┘
                               │
                            carrier lost
                               │
                               ▼
                           ┌──────┐
                           │ lost │
                           └──────┘
```

### Inspection (terminal, no transitions)

```
  Created with one of:
  excellent → good → fair → poor → unusable
  (single assignment, no state machine)
```

### Refund Status

```
  ┌─────────┐             ┌──────────┐             ┌───────────┐
  │ pending │ ──approve──►│ approved │ ──process──►│ processed │
  └─────────┘             └──────────┘             └───────────┘
      │
      │ policy violation
      ▼
  ┌──────────┐
  │ rejected │
  └──────────┘
  
  Any duplicate refund attempt → status: duplicate
```

---

## 6. Bridge / Audit Tables

### StateTransitionLog

Acts as an event log / audit trail. Every time a status field changes on a core entity, one row is appended here. It is **append-only** (no updates, no deletes).

```
(entity_type, entity_id) ──► Polymorphic FK to any entity
```

Allowed entity_types: `ReturnRequest`, `ReturnAuthorization`, `ReturnShipment`, `Inspection`, `Refund`

### AnomalyRecord

Loaded from `data/ground_truth.csv`. Stores labeled anomalies for evaluation purposes.

```
(entity_type, entity_id) ──► Polymorphic reference
anomaly_type              ──► One of 6 ground-truth labels
is_confirmed = true       ──► Ground truth positive
```

This table is **read-only** after seeding — it represents the ground truth used for evaluating anomaly detection algorithms.
