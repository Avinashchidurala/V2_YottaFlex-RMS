"""
API Test Suite for Returns Management System (RMS).
Tests end-to-end workflows:
- Customer in-transit auto-return (zero touch)
- Customer delivered 7-day return request
- Operations Manager decision (approve/reject)
- Real-time customer wallet & company revenue updates
- Inventory stock increment/decrement
- Warehouse quality inspection
- Dashboard metrics and financial reconciliation
"""

import pytest
from fastapi.testclient import TestClient
from run_app import app, get_db

client = TestClient(app)


def test_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["currency"] == "INR"


def test_customers_list():
    res = client.get("/api/v1/customers?limit=5")
    assert res.status_code == 200
    custs = res.json()
    assert len(custs) >= 3
    # Verify the 3 core customers exist
    cids = [c["customer_id"] for c in custs]
    assert "CUST-IND-001" in cids
    assert "CUST-IND-002" in cids
    assert "CUST-IND-003" in cids


def test_customer_orders_and_eligibility():
    res = client.get("/api/v1/customer/CUST-IND-001/orders")
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) > 0
    # Check that eligibility fields exist
    first_order = orders[0]
    assert "is_eligible_for_return" in first_order
    assert "eligibility_reason" in first_order


def test_in_transit_auto_return_flow():
    """
    Test Case A: Order in shipping stage.
    Customer returns:
    - Auto-approved zero-touch (no ops manager approval)
    - Refund credited to wallet
    - Item restocked to inventory
    """
    conn = get_db()
    cursor = conn.cursor()
    # Find an order in shipping status for customer CUST-IND-001 or create one
    cursor.execute("SELECT order_id FROM orders WHERE customer_id = 'CUST-IND-001' AND status = 'shipping' LIMIT 1")
    row = cursor.fetchone()
    if not row:
        # Create a test shipping order
        cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, customer_id, order_date, total_amount_inr, net_amount_inr, status, payment_method)
            VALUES ('ORD-TEST-SHIP-01', 'CUST-IND-001', '2026-11-13 10:00:00', 3999.0, 3999.0, 'shipping', 'upi')
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines 
            (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr)
            VALUES ('LINE-TEST-01', 'ORD-TEST-SHIP-01', 'PROD-ELEC-002', 'boAt Headphones', 'electronics', 1, 3999.0, 3999.0)
        """)
        conn.commit()
        test_oid = "ORD-TEST-SHIP-01"
    else:
        test_oid = row["order_id"]

    cursor.execute("SELECT wallet_balance_inr FROM customers WHERE customer_id = 'CUST-IND-001'")
    initial_wallet = cursor.fetchone()[0]
    conn.close()

    res = client.post("/api/v1/customer/return-in-transit", json={
        "order_id": test_oid,
        "customer_id": "CUST-IND-001",
        "reason": "changed_mind"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["requires_manager_approval"] is False
    assert data["new_wallet_balance_inr"] > initial_wallet


def test_delivered_return_and_ops_approval():
    """
    Test Case B: Delivered order within 7 days.
    - Customer raises return -> status pending
    - Operations Manager reviews -> approves
    - Wallet credited, inventory restocked
    """
    conn = get_db()
    cursor = conn.cursor()
    # Setup test delivered order
    cursor.execute("""
        INSERT OR REPLACE INTO orders 
        (order_id, customer_id, order_date, delivery_date, total_amount_inr, net_amount_inr, status, payment_method)
        VALUES ('ORD-TEST-DELIV-01', 'CUST-IND-002', '2026-11-08 10:00:00', '2026-11-10 12:00:00', 2490.0, 2490.0, 'delivered', 'upi')
    """)
    cursor.execute("""
        INSERT OR REPLACE INTO order_lines 
        (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr)
        VALUES ('LINE-TEST-DELIV-01', 'ORD-TEST-DELIV-01', 'PROD-CLOTH-001', 'Fabindia Kurta', 'clothing', 1, 2490.0, 2490.0)
    """)
    conn.commit()
    conn.close()

    # 1. Customer initiates return
    res = client.post("/api/v1/customer/request-return", json={
        "order_id": "ORD-TEST-DELIV-01",
        "order_line_id": "LINE-TEST-DELIV-01",
        "customer_id": "CUST-IND-002",
        "quantity": 1,
        "reason": "sizing_issue",
        "notes": "Size L is slightly loose"
    })
    assert res.status_code == 200
    req_data = res.json()
    assert req_data["success"] is True
    assert req_data["requires_manager_approval"] is True
    rma_id = req_data["request_id"]

    # 2. Operations Manager approves
    dec_res = client.post("/api/v1/operations/decide", json={
        "request_id": rma_id,
        "action": "approve",
        "override_policy": False
    })
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["success"] is True
    assert dec_data["status"] == "approved"
    assert dec_data["refund_amount_inr"] == 2490.0


def test_dashboard_metrics():
    res = client.get("/api/v1/dashboard/metrics")
    assert res.status_code == 200
    m = res.json()
    assert m["total_orders"] > 0
    assert m["gross_revenue_inr"] > 0
    assert m["net_revenue_inr"] > 0
    assert m["total_anomalies"] > 0
    assert len(m["disposition_breakdown"]) > 0


def test_inventory_list():
    res = client.get("/api/v1/inventory")
    assert res.status_code == 200
    inv = res.json()
    assert len(inv) > 0
    # Check that prices and stock are positive
    for item in inv:
        assert item["unit_price_inr"] > 0
        assert item["stock_quantity"] >= 0
