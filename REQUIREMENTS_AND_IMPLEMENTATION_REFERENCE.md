# Requirements & Implementation Reference Manual
## Returns Management System (RMS) — Full Coding Challenge & Domain Specification

This comprehensive reference document maps every single requirement, business rule, algorithmic step, and real-world industry practice gap filled in the **Returns Management System (RMS)** project.

---

## 1. Business Context / Problem Statement

| Item | Specification | Implementation in RMS |
|---|---|---|
| **Problem Domain** | Reverse logistics and financial reconciliation for e-commerce and retail. | End-to-end lifecycle managing customer returns from initiation through disposition and refund accounting. |
| **Currency** | **INR (Indian Rupee - ₹)** | Standardized across all models, database tables, and UI views. |
| **Core Workflow** | Return eligibility → Authorization → Inbound shipment → Physical inspection → Restocking → Refund → Disposition. | Enforced deterministically through relational database states and REST APIs. |

---

## 2. Objective and Scope

- **Expose Key Decisions**: Real-time eligibility checks (7-day delivered window vs. zero-touch in-transit return), Operations Manager approval/rejection, inspection grading, and inventory routing.
- **Preserve Traceability**: Immutable event log in `state_transition_log.csv` capturing every state jump, actor identity, timestamp, and justification.
- **Produce Measurable Outputs**: Financial metrics (Gross Revenue, Total Refunds, Net Company Revenue, Return Rate %), inventory stock movements, and recovery valuation in INR.

---

## 3. Primary Actors & System Roles

### 👤 Actor 1: Customer (3 Sample Profiles)
- Customer panel features dynamic switching between **3 sample customers**:
  1. `CUST-001` (`CUST-IND-001`): **John Smith** (Bangalore, VIP Tier, Starting Wallet: ₹25,000.00)
  2. `CUST-002` (`CUST-IND-002`): **Sarah Johnson** (Mumbai, Premium Tier, Starting Wallet: ₹18,500.00)
  3. `CUST-003` (`CUST-IND-003`): **Michael Brown** (Delhi, Standard Tier, Starting Wallet: ₹12,000.00)
- Capabilities:
  - Dynamic profile, order history, active returns, eligible returns, and live **Customer Wallet Balance (₹)** that updates immediately when switching.
  - Review purchase orders in `shipping` or `delivered` states.
  - **In-Transit Instant Return**: 1-click zero-touch cancellation with instant wallet credit.
  - **Delivered 7-Day Return**: Submit return request with reason; informed that refund will credit upon company approval.

### 🛠️ Actor 2: Operations Manager
- Reviews the **Pending Approvals Queue** for delivered goods.
- Decision paths:
  - **Approve**: Automatically credits customer wallet (+₹), debits company revenue (-₹), restocks inventory (+Stock), and generates authorization `AUTH-2026-NNNNNN`.
  - **Reject**: Enforces policy exclusion, records reason, and blocks payouts.
- Policy Override: Can authorize returns past the 7-day window for VIP customers with documented rationale.

### 📦 Actor 3: Store / Warehouse Operator
- Receives inbound physical shipments (`RTS-2026-NNNNNN`).
- Performs quality inspection across 5 condition grades: `excellent`, `good`, `fair`, `poor`, `unusable`.
- Routes disposition: `restock`, `refurbish`, `quarantine`, `scrap`.

### 📊 Actor 4: Merchandising & E-Commerce Analyst
- Monitors executive KPIs:
  $$\text{Net Revenue} = \text{Gross Order Revenue} - \text{Total Processed Refunds}$$
  $$\text{Return Rate \%} = \left(\frac{\text{Total Return Requests}}{\text{Total Orders}}\right) \times 100$$
- Visual charts: Category return distribution, disposition breakdown, return reasons frequency.
- **Ground Truth Anomaly Radar**: Real-time fraud and policy violation detection.

---

## 4. Business Workflow & Rules (Points 1 to 5)

### Rule 1: Master Data Precedence
- Master entities are generated first (`Customer`, `Inventory`, `Order`, `OrderLine`).
- Dependent transactions (`ReturnRequest`, `ReturnLine`, `ReturnAuthorization`, `ReturnShipment`, `Inspection`, `Refund`, `InventoryDisposition`) reference existing, valid parent primary keys.

### Rule 2: Foreign Key Integrity
- Every child row strictly references an existing parent ID:
  - `orders.customer_id` $\rightarrow$ `customers.customer_id`
  - `order_lines.order_id` $\rightarrow$ `orders.order_id`
  - `return_requests.order_id` $\rightarrow$ `orders.order_id`
  - `return_lines.request_id` $\rightarrow$ `return_requests.request_id`
  - `return_lines.order_line_id` $\rightarrow$ `order_lines.line_id`
  - `return_authorizations.request_id` $\rightarrow$ `return_requests.request_id`
  - `return_shipments.auth_id` $\rightarrow$ `return_authorizations.auth_id`
  - `inspections.shipment_id` $\rightarrow$ `return_shipments.shipment_id`
  - `refunds.request_id` $\rightarrow$ `return_requests.request_id`
  - `inventory_dispositions.inspection_id` $\rightarrow$ `inspections.inspection_id`

### Rule 3: Differentiated Business Logic & Industry Practice Gaps Filled

#### A) In-Transit Returns (Shipping Stage — Zero-Touch)
- If `order.status == 'shipping'`:
  - Customer return is **auto-approved immediately**.
  - **Operations Manager approval is NOT required**.
  - Customer wallet is credited directly (+₹).
  - Company revenue is decremented (-₹).
  - Product is immediately added back to active inventory stock (+1 Qty).
  - Status logged as `auto_refunded_in_transit`.

#### B) Delivered Goods (7-Day Policy Window)
- If `order.status == 'delivered'`:
  - System verifies: $\text{days\_since\_delivery} \le 7$.
  - If $\le 7$ days: Return request is created with status `pending`.
  - Customer is shown: *"Return request raised. Refund will be credited once the company approves."*
  - Forwarded to Operations Manager for review.
  - If $> 7$ days: Request is blocked as policy expired unless manager override is flagged.

#### C) Refund Math Reconciliation
$$\text{Gross Refund (INR)} = \text{Approved Qty} \times \text{Unit Price} \times \left(1 - \frac{\text{Discount \%}}{100}\right)$$
$$\text{Restocking Fee} = \begin{cases} 5\% \times \text{Gross Refund} & \text{if condition} \in \{\text{fair, poor}\} \\ 0 & \text{otherwise} \end{cases}$$
$$\text{Shipping Fee} = \begin{cases} ₹0 & \text{if reason} \in \{\text{defective, damaged\_in\_transit, wrong\_item}\} \\ ₹100 & \text{otherwise (e.g. changed mind, sizing)} \end{cases}$$
$$\text{Net Refund (INR)} = \max(0, \text{Gross Refund} - \text{Restocking Fee} - \text{Shipping Fee})$$

#### D) Disposition Routing & Estimated Recovery Value
| Condition Grade | Default Disposition Action | Estimated Recovery Rate (% of Unit Price) |
|---|---|---|
| `excellent` | `restock` (A-grade inventory) | 90% |
| `good` | `restock` (B-grade inventory) | 90% |
| `fair` | `refurbish` (repair & repackage) | 50% |
| `poor` | `quarantine` (vendor return) | 20% |
| `unusable` | `scrap` (salvage / recycle) | 5% |

### Rule 4: Audit Trail Immutability
- State transitions are recorded in `state_transition_log.csv` as discrete append-only events.
- Original timestamps and status changes are preserved.

### Rule 5: Ground Truth Separation
- Deliberate anomalies are isolated in `ground_truth.csv`.
- Anomaly labels are never leaked into the input features of core business tables.

---

## 5. Entities, Keys, and Relationships

```
┌──────────────┐         ┌──────────────┐         ┌──────────────────┐
│   Customer   │ 1     N │    Order     │ 1     N │    OrderLine     │
│ ──────────── │────────►│ ──────────── │────────►│ ──────────────── │
│ customer_id  │         │ order_id     │         │ line_id          │
│ name         │         │ customer_id  │         │ order_id         │
│ wallet_inr   │         │ net_amount   │         │ unit_price_inr   │
└──────────────┘         └──────┬───────┘         └─────────┬────────┘
                                │ 1                         │
                                │ N                         │ N
                                ▼                           │
                     ┌─────────────────────┐                │
                     │    ReturnRequest    │◄───────────────┘
                     │ ─────────────────── │       (via ReturnLine)
                     │ request_id (RMA-)   │
                     │ customer_id         │
                     │ order_id            │
                     │ days_since_delivery │
                     └──────────┬──────────┘
                                │
               ┌────────────────┼────────────────┐
               │ 1              │ 1              │ 1
               ▼                ▼                ▼
      ┌────────────────┐ ┌───────────────┐ ┌────────────────────┐
      │   ReturnLine   │ │    Refund     │ │ReturnAuthorization │
      │ ────────────── │ │ ───────────── │ │ ────────────────── │
      │ line_id (RMAL) │ │ refund_id(REF)│ │ auth_id (AUTH-)    │
      │ request_id     │ │ request_id    │ │ request_id (UNIQUE)│
      │ requested_qty  │ │ net_refund_inr│ └─────────┬──────────┘
      │ approved_qty   │ └───────────────┘           │ 1
      └────────────────┘                             ▼
                                           ┌────────────────────┐
                                           │   ReturnShipment   │
                                           │ ────────────────── │
                                           │ shipment_id (RTS-) │
                                           │ auth_id            │
                                           └─────────┬──────────┘
                                                     │ 1
                                                     ▼
                                           ┌────────────────────┐
                                           │    Inspection      │
                                           │ ────────────────── │
                                           │ inspection_id      │
                                           │ shipment_id        │
                                           └─────────┬──────────┘
                                                     │ 1
                                                     ▼
                                           ┌────────────────────┐
                                           │InventoryDisposition│
                                           │ ────────────────── │
                                           │ disposition_id     │
                                           │ inspection_id      │
                                           │ disposition_action │
                                           └────────────────────┘
```

---

## 6. ID & Nomenclature Conventions

Strict deterministic naming format with zero-padded counters:

| Entity | Format Pattern | Example |
|---|---|---|
| **Customer** | `CUST-IND-NNN` | `CUST-IND-001` |
| **Order** | `ORD-YYYY-NNNNNN` | `ORD-2026-000001` |
| **OrderLine** | `LINE-ORD-YYYY-NNNNNN-NN` | `LINE-ORD-2026-000001-01` |
| **ReturnRequest** | `RMA-YYYY-NNNNNN` | `RMA-2026-000001` |
| **ReturnLine** | `RMAL-RMA-YYYY-NNNNNN-NN` | `RMAL-RMA-2026-000001-01` |
| **ReturnAuthorization** | `AUTH-YYYY-NNNNNN` | `AUTH-2026-000001` |
| **ReturnShipment** | `RTS-YYYY-NNNNNN` | `RTS-2026-000001` |
| **Inspection** | `INSP-YYYY-NNNNNN` | `INSP-2026-000001` |
| **Refund** | `REF-YYYY-NNNNNN` | `REF-2026-000001` |
| **InventoryDisposition** | `DISP-YYYY-NNNNNN` | `DISP-2026-000001` |
| **StateTransitionLog** | `LOG-YYYY-NNNNNN` | `LOG-2026-000001` |
| **AnomalyRecord** | `ANOM-YYYY-NNNNNN` | `ANOM-2026-000001` |

---

## 7. Synthetic Data Generation Instructions (Steps 1 to 10)

### Step 1 — Data Dictionary
Comprehensive field specifications documented in [DATA_DICTIONARY.md](file:///c:/Users/avina/Downloads/Avi_Yotta_flex/DATA_DICTIONARY.md) including types, constraints, and validation rules.

### Step 2 — Parent-First Creation & Generation Logic
Parent master tables (`customers`, `inventory`, `orders`, `order_lines`) are generated before child transaction records.

### Step 3 — Deterministic IDs & Seed
Deterministic PRNG initialized with fixed seed `20261022`. Counters are sequential and immutable.

### Step 4 — Baseline Volume & Coverage
| Dataset | Row Count | Purpose |
|---|---|---|
| `customers.csv` | **3** | Exactly the 3 core customer profiles for panels |
| `inventory.csv` | **14** | Products with pricing, stock counts, and GST % |
| `orders.csv` | **30,000** | Full scale purchase transactions |
| `order_lines.csv` | **54,163** | Items ordered across all 30k orders |
| `return_requests.csv` | **5,000** | Return requests (~16.7% return rate) |
| `return_lines.csv` | **8,000** | Exactly 8,000 return lines distributed across requests |
| `return_authorizations.csv` | **3,352** | Authorized return requests |
| `return_shipments.csv` | **3,352** | Inbound transit records |
| `inspections.csv` | **3,332** | Quality inspection gradings |
| `refunds.csv` | **4,117** | Wallet refund transactions in INR |
| `inventory_dispositions.csv` | **4,082** | Post-inspection inventory movements |
| `state_transition_log.csv` | **750** | State change audit events |
| `ground_truth.csv` | **200** | Labelled anomaly instances |

### Step 5 — Injected Negative Scenarios / Edge Cases
1. **`return_qty_exceeds_purchased`**: Requested return quantity > order line purchased quantity.
2. **`refund_exceeds_paid`**: Net refund amount > original order line paid total.
3. **`restock_before_inspection`**: Inventory disposition timestamp < warehouse inspection timestamp.
4. **`late_return_no_override`**: Return request submitted after 7-day window without an authorized manager override.
5. **`duplicate_refund`**: Multiple payout attempts for the same return request.
6. **`missing_shipment`**: Return shipment marked lost in transit by carrier.

### Step 6 — Derived Values Calculation
Totals, taxes, discounts, net refund amounts, and days since delivery are strictly computed from source columns rather than generated as independent random variables.

### Step 7 — Separate Ground Truth
Ground truth anomalies are written exclusively to `data/ground_truth.csv`.

### Step 8 — Automated Validation
[data_generator/validator.py](file:///c:/Users/avina/Downloads/Avi_Yotta_flex/data_generator/validator.py) checks:
- Primary key uniqueness across all tables.
- Foreign key integrity (no orphan rows).
- Allowed enum values.
- Arithmetic reconciliation of refund payouts.
- Chronological ordering of dates.

### Step 9 — Export Manifest & Validation Summary
All datasets are exported to `./data/` alongside [manifest.json](file:///c:/Users/avina/Downloads/Avi_Yotta_flex/data/manifest.json) and [validation_summary.json](file:///c:/Users/avina/Downloads/Avi_Yotta_flex/data/validation_summary.json).

### Step 10 — Bitwise Reproducibility Verification
Run `python test_reproducibility.py` to regenerate the full dataset in two independent passes. Every file achieves a 100% SHA256 bitwise match.

---

## 8. Validation Rules & Acceptance Criteria

- **Eligibility Policy**: Returns within 7 days of delivery are eligible; returns past 7 days are blocked unless manager override is set.
- **Refund Math Reconciliation**:
  $$\text{Net Refund} = \text{Gross Refund} - \text{Restocking Fee} - \text{Shipping Fee}$$
- **Duplicate Payout Prevention**: Duplicate refund attempts are intercepted, flagged with status `duplicate`, and referenced to the original refund ID.
- **Inventory Balance**: Restocked items increment stock count (+Stock); cancelled shipments are returned to available inventory.

---

## 9. Evaluation Focus & Lawful Provenance

- **Meaningful Distribution**: Orders span electronics, fashion, home appliances, books, jewelry, and sports with Indian pricing tiers.
- **Fixed-Seed Reproducibility**: Seed `20261022` guarantees identical row counts and hashes.
- **Lawful Provenance**: 100% synthetically generated via Python PRNG algorithms. No private, confidential, or web-scraped data used.
- **Public Domain Reference**: Demographic and category structures inspired by public Indian retail classifications.
