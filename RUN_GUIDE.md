# YottaFlex Return Management System (RMS) — Complete Operation & Run Guide

This guide provides end-to-end instructions for running, operating, and verifying the **YottaFlex Return Management System (RMS)**.

---

## 1. System Requirements & Prerequisites

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.10, 3.11, or 3.12+ (Standard library `sqlite3` and `unittest` included)
- **Dependencies**:
  ```bash
  pip install fastapi uvicorn pandas pydantic
  ```
- **Port**: Port `8000` available on `localhost`.

---

## 2. Quickstart: Running the Application

### Start the Server (Single Command)
From the root of the project folder:
```bash
python run_app.py
```
*(Alternatively: `python app.py`)*

Output confirms startup:
```text
=====================================================================
[*] YottaFlex Return Management System (RMS) Enterprise Server
[*] Database: ./data/rms.db
[*] Application Dashboard: http://localhost:8000
[*] Swagger API Documentation: http://localhost:8000/docs
=====================================================================
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Accessing the Web Application
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

### Accessing the REST API Documentation (Swagger UI)
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 3. Running Automated Tests & Verification

### A. Run Full Test Suite (12 Unit Tests)
Validates generator reproducibility, schema constraints, REST API workflows, policy rules, and financial math reconciliation:
```bash
python run_tests.py
```
**Expected Output**:
```text
............
Ran 12 tests in ~1.5s
OK
```

### B. Verify 100% Bitwise Reproducibility (Deterministic Seed `20261022`)
Regenerates the complete dataset in two isolated passes and compares SHA256 checksums:
```bash
python test_reproducibility.py
```
**Expected Output**:
```text
[✓] 14/14 datasets match 100% bitwise across independent passes.
```

### C. Seed or Refresh SQLite Database
If you ever want to re-seed the SQLite database (`data/rms.db`) fresh from the master CSV files:
```bash
python seed_database.py --clear
```

---

## 4. Guided Walkthrough of the 5 Role Dashboards

The application features a dark navy navigation sidebar / top bar allowing instant switching between all 5 enterprise roles:

### Role 1: Customer Portal (`1. Customer`)
- **Dynamic Customer Switching**:
  - Use the customer dropdown at the top:
    * `John Smith (CUST-001)` — Bangalore, VIP Tier
    * `Sarah Johnson (CUST-002)` — Mumbai, Premium Tier
    * `Michael Brown (CUST-003)` — Delhi, Standard Tier
  - Switching immediately refreshes orders, active returns, eligible returns, wallet balance, and refund history from real database records.
- **My Orders**:
  - Displays orders with status badges:
    * **Delivered ≤ 7 days**: Green `Eligible (X days left)` badge with "Request Return" button.
    * **Shipping stage**: Blue `In-Transit` badge with "Cancel & Instant Refund" button.
    * **Delivered > 7 days**: Grey `Expired` badge.
    * **Non-returnable items**: Orange `Policy Exclusion` badge.
- **Request a Return**:
  - Click "Request Return" on an eligible order line, choose a reason (e.g., *Defective*, *Changed mind*), add comments, and submit.
  - An `RMA-2026-NNNNNN` request is generated with status `pending`, routed to Operations Manager.
- **In-Transit Instant Cancellation (Rule A)**:
  - Click "Cancel & Instant Refund" on any in-transit order.
  - Instant zero-touch return: customer wallet is credited (+₹) immediately, company revenue decremented, and inventory restocked without requiring manager approval.
- **Refund Tracking**:
  - Displays all refunds with `REF-2026-NNNNNN` ID, payment method (`customer_wallet`), and amount in INR (₹).

### Role 2: Operations Manager (`2. Operations`)
- **Review Queue**:
  - Filter returns by status: `Pending`, `Approved`, `Rejected`, `Overrides`, or `All`.
- **Approve / Reject Decisions**:
  - Click **Approve Return**: Updates return to `approved`, credits customer wallet (+₹), creates `AUTH-` authorization and `RTS-` return shipment for warehouse intake.
  - Click **Reject Return**: Prompts for rejection reason and updates record to `rejected` without wallet credit.
- **Executive Policy Override**:
  - Check the "Policy Override" toggle and enter justification to approve exceptions (e.g., VIP customer courtesy for an order delivered past the 7-day window).

### Role 3: Store / Warehouse Operator (`3. Warehouse`)
- **Inbound RTS Intake**:
  - View incoming return shipments (`RTS-2026-NNNNNN`) handled by BlueDart, Delhivery, DTDC.
  - Click **Receive Shipment** to mark as arrived at the warehouse dock.
- **Physical Quality Inspection & Grading**:
  - Grade the product condition:
    * **Grade A – Like New** (Recovery: 90%)
    * **Grade B – Good** (Recovery: 90%)
    * **Grade C – Damaged** (Recovery: 50%)
    * **Grade D – Unsellable** (Recovery: 5%)
- **Disposition Routing (Inventory Control)**:
  - Choose disposition action: `Restock`, `Refurbish`, `Quarantine`, or `Scrap`.
  - **Inventory Movement Rule**: Selecting `Restock` increments sellable warehouse stock (`stock_quantity += qty`). Selecting `Refurbish`, `Quarantine`, or `Scrap` routes the item away to repair or salvage bins without inflating sellable stock.
- **Real-Time Restocked Inventory Catalog**:
  - View live warehouse stock counts and bin allocations updating dynamically.

### Role 4: Merchandising & E-Commerce Analyst (`4. Analytics`)
- **Executive KPIs**:
  - Gross Revenue, Total Refunds, Net Revenue in INR (₹), and Return Rate %.
- **4 Interactive Visualizations**:
  - Monthly Return Trends vs Orders.
  - Inventory Disposition Fate Distribution (Restock vs Refurbish vs Scrap).
  - Return Reasons Breakdown (Defective, Changed Mind, Sizing, etc.).
  - Quality Grade Distribution (Grade A through D).
- **Synthetic Ground Truth Anomaly Radar**:
  - Identifies policy violations, over-refunds, and duplicate payout attempts.
  - 1-click **Export CSV** button to download the anomalies table.

### Role 5: Admin Master Dashboard (`5. Admin Master`)
- **Comprehensive Database Access**:
  - Select any of the 13 core tables: `customers`, `inventory`, `orders`, `order_lines`, `return_requests`, `return_lines`, `return_authorizations`, `return_shipments`, `inspections`, `refunds`, `inventory_dispositions`, `audit_logs`, `anomalies`.
- **Full CRUD Operations**:
  - Search records with debounce filtering across columns.
  - **Add Record**: Opens a dynamic modal with form inputs matching that table's exact schema.
  - **Edit Record**: Updates any selected record by primary key.
  - **Delete Record**: Single row delete or multi-select bulk delete.
- **Download Table Template (CSV/Excel)**:
  - Click "Download Template" to download a CSV with column headers and a pre-populated sample row.
- **Upload Bulk Data (CSV/Excel)**:
  - Drop a CSV file to bulk-insert records directly into the SQLite database.

---

## 5. Core Business Rules Enforced

1. **Rule 1: Master Data Precedence**: Customers, Inventory, Orders, and OrderLines are created first. All transaction tables reference existing parent IDs.
2. **Rule 2: Foreign Key Integrity**: Zero orphan records across all 13 tables.
3. **Rule 3.A: In-Transit Returns**: Zero-touch auto-approved return without manager intervention.
4. **Rule 3.B: 7-Day Policy Window**: Delivered orders $\le 7$ days require Operations Manager review. Returns $> 7$ days are blocked unless executive policy override is authorized.
5. **Rule 3.C: Refund Math Reconciliation**:
   $$\text{Gross Refund} = \text{Unit Price} \times (1 - \text{Discount}) \times (1 + \text{GST}) \times \text{Approved Qty}$$
   $$\text{Net Refund} = \max(0, \text{Gross Refund} - \text{Restocking Fee} - \text{Shipping Fee})$$
6. **Rule 3.D: Disposition Controls Inventory**: Only `Restock` disposition increments sellable stock. `Scrap`, `Quarantine`, and `Refurbish` route items to salvage or holding bins.
7. **Rule 3.E: Duplicate Payouts Blocked**: Second approval or refund on the same return is blocked (`HTTP 400`), logged with `is_duplicate = 1`, and customer wallet is protected from double crediting.
8. **Rule 4: Immutable Audit Trail**: Every status transition is logged in `state_transition_log` with timestamp, actor, and justification.
9. **Rule 5: Ground Truth Separation**: Anomalies are isolated in `ground_truth.csv` without leaking into training features.
10. **Rule 6: Currency**: Standardized strictly in **Indian Rupees (INR - ₹)**.
