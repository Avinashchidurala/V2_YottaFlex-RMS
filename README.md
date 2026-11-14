# Returns Management System (RMS) - End-to-End Reverse Logistics & Finance

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Currency](https://img.shields.io/badge/Currency-INR%20₹-orange)
![Deterministic Seed](https://img.shields.io/badge/Seed-20261022-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Executive Summary

The **Returns Management System (RMS)** is a comprehensive, production-ready, full-stack reverse logistics and financial reconciliation platform built specifically for Indian retail and e-commerce ecosystems.

It solves the core operational challenge: **Managing return eligibility, return authorization, physical inspection, restocking, financial refunds, and inventory disposition with 100% financial traceability in INR (₹).**

### Key Problem Solved & Real-Time Industry Practice Gaps Filled
1. **Interactive Multi-Actor Workflow (5 Enterprise Dashboards)**:
   - **Role 1: Customer Portal**: Switchable dynamically between **3 Sample Customer Profiles**:
     * **Customer 1**: John Smith (`CUST-001` / `CUST-IND-001`, VIP Tier, Starting Wallet: ₹25,000.00)
     * **Customer 2**: Sarah Johnson (`CUST-002` / `CUST-IND-002`, Premium Tier, Starting Wallet: ₹18,500.00)
     * **Customer 3**: Michael Brown (`CUST-003` / `CUST-IND-003`, Standard Tier, Starting Wallet: ₹12,000.00)
     All dashboard metrics, orders, returns, and wallet balances update dynamically upon selection.
   - **Role 2: Operations Manager**: Approval/rejection queue with one-click decision-making, executive policy override for late returns, and automatic accounting ledger adjustments.
   - **Role 3: Store/Warehouse Operator**: Inbound physical shipment intake (`RTS-2026-NNNNNN`), physical inspection quality grading (Grade A, B, C, D), and disposition routing (`Restock`, `Refurbish`, `Quarantine`, `Scrap`).
   - **Role 4: Merchandising/E-Commerce Analyst**: Real-time KPI analytics, financial reconciliation (Gross Revenue vs. Refunds vs. Net Revenue in INR ₹), return reasons breakdown, and ground-truth anomaly detection.
   - **Role 5: Admin Master Dashboard**: Comprehensive database management across all 13 tables, full CRUD (Add/Edit/Delete), downloadable CSV/Excel table templates, and bulk CSV data ingestion.
   - **Live Warehouse Inventory & Financial Ledger**: Real-time stock counts that dynamically decrement upon purchase and update based on physical quality inspection disposition.

2. **Differentiated Business Rules (Real-Time Industry Practices)**:
   - ⚡ **Rule A: In-Transit Returns (Shipping Stage)**:
     - When a customer cancels/returns while the product is still in the `shipping` stage (Return-to-Origin):
     - **Operations approval is NOT required** (Zero-touch automated return)!
     - Immediate refund credited to the customer's wallet.
     - Immediate company revenue deduction.
     - Item automatically added back to active inventory stock.
   - 🛡️ **Rule B: Delivered Items (7-Day Policy Window)**:
     - If `days_since_delivery <= 7`: Customer can raise a return request.
     - Customer is explicitly informed: *"Your return request is raised. Refund will be credited to your wallet once the company/operations manager approves."*
     - Request moves to the **Operations Manager Queue** with status `PENDING_APPROVAL`.
     - Upon Manager Approval: Customer wallet is credited (+₹), Company revenue is deducted (-₹), and item is restocked/routed to disposition.
     - If `days_since_delivery > 7`: Return request is blocked automatically ("Return window expired - past 7 days") unless an authorized manager override is provided.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   RETURNS MANAGEMENT SYSTEM (RMS)                        │
└──────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────────────────────────────────────────────┐
     │                CUSTOMER INITIATES RETURN                     │
     └──────────────────────────────┬───────────────────────────────┘
                                    │
                    Order Status / Timing Check?
                                    │
          ┌─────────────────────────┴────────────────────────┐
          │                                                  │
    [Shipping Stage]                                [Delivered Stage]
          │                                                  │
          ▼                                                  ▼
 ┌─────────────────────────┐                        Days <= 7 Days?
 │ ZERO-TOUCH AUTO RETURN  │                        ├── Yes ──► Move to Ops Manager Queue
 │ (No Ops Approval Req.)  │                        └── No  ──► Policy Expired (Blocked)
 └────────┬────────────────┘                                         │
          │                                                          ▼
          │                                                 ┌───────────────────┐
          │                                                 │ Operations Manager│
          │                                                 │ Decides Approve / │
          │                                                 │ Reject            │
          │                                                 └─────────┬─────────┘
          │                                                           │
          ├───────────────────────────┬───────────────────────────────┘
          │ (Approved)                │ (Approved)
          ▼                           ▼
 ┌───────────────────┐       ┌────────────────────────┐
 │ Customer Wallet   │       │ Real-Time Company      │
 │ Credited (+₹ INR) │       │ Revenue Deducted (-₹)  │
 └───────────────────┘       └────────────────────────┘
          │
          ▼
 ┌───────────────────┐       ┌────────────────────────┐
 │ Inbound Shipment  │──────►│ Warehouse Inspection   │
 │ (RTS-2026-NNNNNN) │       │ (Quality Grading)      │
 └───────────────────┘       └───────────┬────────────┘
                                         │
                                         ▼
                             ┌────────────────────────┐
                             │ Inventory Disposition  │
                             │ • Restock (+Stock)     │
                             │ • Refurbish (50% rec.) │
                             │ • Quarantine (Vendor)  │
                             │ • Scrap (Write-off)    │
                             └────────────────────────┘
```

---

## Quick Start (Run in 1 Minute)

### 1. Requirements
- Python 3.10+ (Standard library `sqlite3` and `unittest` included)
- Installed dependencies: `fastapi`, `uvicorn`, `pandas` (already available in requirements)

### 2. Start the RMS Application Server
Run the single command:
```bash
python run_app.py
```

### 3. Open the Interactive Dashboards
- **Web Application**: Open [http://localhost:8000](http://localhost:8000) in any browser.
  - Switch between all 4 actor roles in tabs.
  - Test live wallet updates and instant in-transit cancellations.
  - Approve or reject return requests as Operations Manager.
  - Inspect shipments and route dispositions as Warehouse Operator.
  - View financial ledger and anomaly radar as Analyst.
- **Interactive REST API Docs (Swagger UI)**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Automated Testing & 100% Reproducibility

### Run the Full Test Suite
Executes unit tests, REST API tests, workflow tests, policy rules, and mathematical reconciliation:
```bash
python run_tests.py
```
*Result: 12/12 tests pass with `OK`.*

### Verify Bitwise Reproducibility (Step 10 Requirement)
Demonstrates that regenerating twice with fixed seed `20261022` produces 100% identical SHA256 checksums across every single dataset:
```bash
python test_reproducibility.py
```
*Result: 14/14 files match 100% bitwise.*

### Regenerate Baseline Synthetic Datasets
Generate full volume (30,000 orders, 5,000 returns, 8,000 return lines, 14 products, 1,000 customers) and run automated validation:
```bash
python run_generator.py --scale 1.0
```

### Seed SQLite Database from CSVs
Loads all generated CSV records into `data/rms.db` respecting relational foreign keys:
```bash
python seed_database.py --clear
```

---

## 3 Core Customer Profiles

| Customer ID | Name | City | Tier | Starting Wallet | Purpose |
|---|---|---|---|---|---|
| `CUST-IND-001` | **Rahul Sharma** | Bangalore | VIP | ₹25,000.00 | Tests in-transit instant cancellations & high-value VIP orders |
| `CUST-IND-002` | **Priya Patel** | Mumbai | Premium | ₹18,500.00 | Tests 7-day delivered return requests & manager approvals |
| `CUST-IND-003` | **Arjun Verma** | Delhi | Standard | ₹12,000.00 | Tests standard policy limits & category return windows |

---

## Synthetic Data Volume & Coverage

| Entity | Primary Key Format | Baseline Volume | Description |
|---|---|---|---|
| **Customer** | `CUST-IND-NNN` | 1,000 | Customers with wallet balances across Indian cities |
| **Inventory** | `PROD-CAT-NNN` | 14 | Products with INR pricing, stock levels, GST %, return windows |
| **Order** | `ORD-2026-NNNNNN` | 30,000 | Purchase transactions (delivered, shipping, confirmed) |
| **OrderLine** | `LINE-ORD-NNNNNN-NN` | ~54,000 | Individual items, quantities, discounts, and GST |
| **ReturnRequest** | `RMA-2026-NNNNNN` | 5,000 | Return requests (auto-approved in-transit, delivered pending) |
| **ReturnLine** | `RMAL-RMA-NNNNNN-NN` | 5,000 | Line-level return items, requested vs approved qty |
| **ReturnAuthorization** | `AUTH-2026-NNNNNN` | 3,370 | 14-day return authorization passes |
| **ReturnShipment** | `RTS-2026-NNNNNN` | 3,370 | Physical transit via BlueDart, Delhivery, DTDC |
| **Inspection** | `INSP-2026-NNNNNN` | 3,350 | Warehouse quality assessment (excellent/good/fair/poor/unusable) |
| **Refund** | `REF-2026-NNNNNN` | 4,135 | Financial reimbursement to customer wallet in INR |
| **InventoryDisposition** | `DISP-2026-NNNNNN` | 4,100 | Fate: Restock, Refurbish, Quarantine, Scrap with recovery INR |
| **StateTransitionLog** | `LOG-2026-NNNNNN` | 750 | Audit trail of status transitions |
| **AnomalyRecord** | `ANOM-2026-NNNNNN` | 200 | Ground-truth labelled negative scenarios in `ground_truth.csv` |

---

## Injected Negative Scenarios / Edge Cases (Ground Truth)

All edge cases are labelled in `data/ground_truth.csv` and never leak into features:

1. **`return_qty_exceeds_purchased`**: Requested return quantity strictly exceeds the original purchased order line quantity.
2. **`refund_exceeds_paid`**: Net refund amount exceeds the total paid amount for the order line.
3. **`restock_before_inspection`**: Inventory disposition timestamp chronologically precedes the inspection timestamp.
4. **`late_return_no_override`**: Return requested after the 7-day policy window has elapsed without an authorized manager override.
5. **`duplicate_refund`**: Duplicate payout attempted for the same return request; flagged and blocked.
6. **`missing_shipment`**: Return shipment marked as lost in transit by the carrier.

---

## REST API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check & system time |
| `GET` | `/api/v1/customers` | List customers (including 3 core profiles) |
| `GET` | `/api/v1/customer/{customer_id}/orders` | Customer order history with 7-day eligibility calculation |
| `POST` | `/api/v1/customer/return-in-transit` | **Rule A**: Zero-touch auto return for shipping stage orders |
| `POST` | `/api/v1/customer/request-return` | **Rule B**: Submit delivered item return (7-day window) |
| `GET` | `/api/v1/operations/pending-requests` | Fetch pending return requests queue for Operations Manager |
| `POST` | `/api/v1/operations/decide` | Approve or reject return request (updates wallet & inventory) |
| `GET` | `/api/v1/warehouse/shipments` | List inbound return shipments (RTS-...) |
| `POST` | `/api/v1/warehouse/inspect` | Record quality inspection & disposition routing |
| `GET` | `/api/v1/inventory` | Real-time warehouse product stock catalog |
| `GET` | `/api/v1/dashboard/metrics` | Financial ledger: Gross Revenue, Refunds, Net Revenue, KPIs |

---

## Lawful Provenance & License

- **Synthetic Data**: 100% synthetically generated via deterministic PRNG algorithms using fixed seed `20261022`. No private or copyright-protected data collected.
- **License**: MIT Open Source License.
