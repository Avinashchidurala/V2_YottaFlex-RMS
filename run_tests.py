#!/usr/bin/env python3
"""
Test Runner using Python standard library unittest.
Zero external test dependencies required.
Executes:
1. Generator reproducibility & schema validation
2. Edge cases verification in ground_truth.csv
3. REST API endpoint tests & multi-actor workflows
4. Arithmetic reconciliation of refunds & wallet balances
"""

import unittest
import os
import shutil
import pandas as pd
from fastapi.testclient import TestClient

from run_app import app, get_db
from data_generator.generator import RMSDataGenerator
from data_generator.validator import validate_all


class TestRMSDataGenerator(unittest.TestCase):
    def test_01_small_scale_generation(self):
        """Test generator at small scale and verify file outputs"""
        test_dir = "data_test_unit"
        gen = RMSDataGenerator(seed=20261022, scale=0.01, output_dir=test_dir)
        gen.generate_all()

        expected = [
            "customers.csv", "inventory.csv", "orders.csv", "order_lines.csv",
            "return_requests.csv", "return_lines.csv", "return_authorizations.csv",
            "return_shipments.csv", "inspections.csv", "refunds.csv",
            "inventory_dispositions.csv", "state_transition_log.csv",
            "ground_truth.csv", "manifest.json"
        ]
        for f in expected:
            self.assertTrue(os.path.exists(os.path.join(test_dir, f)), f"Missing file: {f}")

        summary = validate_all(data_dir=test_dir)
        self.assertEqual(summary["status"], "PASSED")
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_02_baseline_dataset_validation(self):
        """Validate existing full dataset in data/"""
        self.assertTrue(os.path.exists("data/orders.csv"), "Baseline dataset missing")
        summary = validate_all(data_dir="data")
        self.assertEqual(summary["status"], "PASSED")
        self.assertEqual(summary["checks"]["fk_integrity"]["status"], "PASSED")
        self.assertTrue(summary["checks"]["refund_math_reconciliation"]["is_valid"])

    def test_03_ground_truth_negative_scenarios(self):
        """Verify all 5 required edge cases are present in ground_truth.csv"""
        gt_path = "data/ground_truth.csv"
        self.assertTrue(os.path.exists(gt_path))
        df = pd.read_csv(gt_path)
        anomaly_types = set(df["anomaly_type"])

        self.assertIn("return_qty_exceeds_purchased", anomaly_types)
        self.assertIn("refund_exceeds_paid", anomaly_types)
        self.assertIn("restock_before_inspection", anomaly_types)
        self.assertIn("late_return_no_override", anomaly_types)
        self.assertIn("duplicate_refund", anomaly_types)


class TestRMSAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_04_health_endpoint(self):
        """Test /api/v1/health returns healthy and currency=INR"""
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["currency"], "INR")

    def test_05_customers_list(self):
        """Test 3 core customers exist in the system"""
        res = self.client.get("/api/v1/customers?limit=5")
        self.assertEqual(res.status_code, 200)
        custs = res.json()
        cids = [c["customer_id"] for c in custs]
        self.assertIn("CUST-IND-001", cids)
        self.assertIn("CUST-IND-002", cids)
        self.assertIn("CUST-IND-003", cids)

    def test_06_in_transit_auto_return(self):
        """Test Case A: Shipping stage cancellation triggers instant auto-refund to wallet"""
        import uuid
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT wallet_balance_inr FROM customers WHERE customer_id = 'CUST-IND-001'")
        init_wallet = cursor.fetchone()[0]

        # Insert a unique test shipping order
        uid = uuid.uuid4().hex[:6]
        test_oid = f"ORD-TEST-INTRANSIT-{uid}"
        test_lid = f"LINE-INTRANSIT-{uid}"
        cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, customer_id, order_date, total_amount_inr, net_amount_inr, status, payment_method)
            VALUES (?, 'CUST-IND-001', '2026-11-13 10:00:00', 5000.0, 5000.0, 'shipping', 'upi')
        """, (test_oid,))
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines 
            (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr)
            VALUES (?, ?, 'PROD-ELEC-002', 'Headphones', 'electronics', 1, 5000.0, 5000.0)
        """, (test_lid, test_oid))
        conn.commit()
        conn.close()

        res = self.client.post("/api/v1/customer/return-in-transit", json={
            "order_id": test_oid,
            "customer_id": "CUST-IND-001",
            "reason": "changed_mind"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["requires_manager_approval"])
        self.assertGreater(data["new_wallet_balance_inr"], init_wallet)

    def test_07_delivered_return_ops_decision(self):
        """Test Case B: Delivered order 7-day request and Operations Manager approval"""
        import uuid
        conn = get_db()
        cursor = conn.cursor()
        uid = uuid.uuid4().hex[:6]
        test_oid = f"ORD-TEST-DELIV-{uid}"
        test_lid = f"LINE-DELIV-{uid}"
        cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, customer_id, order_date, delivery_date, total_amount_inr, net_amount_inr, status, payment_method)
            VALUES (?, 'CUST-IND-002', '2026-11-09 10:00:00', '2026-11-11 12:00:00', 3000.0, 3000.0, 'delivered', 'credit_card')
        """, (test_oid,))
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines 
            (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr)
            VALUES (?, ?, 'PROD-CLOTH-001', 'Kurta', 'clothing', 1, 3000.0, 3000.0)
        """, (test_lid, test_oid))
        conn.commit()
        conn.close()

        # 1. Customer initiates
        res = self.client.post("/api/v1/customer/request-return", json={
            "order_id": test_oid,
            "order_line_id": test_lid,
            "customer_id": "CUST-IND-002",
            "quantity": 1,
            "reason": "defective"
        })
        self.assertEqual(res.status_code, 200)
        req_data = res.json()
        self.assertTrue(req_data["requires_manager_approval"])
        rma_id = req_data["request_id"]

        # 2. Operations Manager approves
        res2 = self.client.post("/api/v1/operations/decide", json={
            "request_id": rma_id,
            "action": "approve"
        })
        self.assertEqual(res2.status_code, 200)
        dec_data = res2.json()
        self.assertEqual(dec_data["status"], "approved")

    def test_08_dashboard_metrics(self):
        """Test KPI aggregations on /api/v1/dashboard/metrics"""
        res = self.client.get("/api/v1/dashboard/metrics")
        self.assertEqual(res.status_code, 200)
        m = res.json()
        self.assertGreater(m["total_orders"], 0)
        self.assertGreater(m["gross_revenue_inr"], 0)
        self.assertGreater(m["net_revenue_inr"], 0)
        self.assertGreater(m["total_anomalies"], 0)

    def test_09_eligibility_policy_enforcement(self):
        """Test eligibility decisions follow policy: non-returnable exclusions, excess quantity, 7-day window"""
        import uuid
        conn = get_db()
        cursor = conn.cursor()
        uid = uuid.uuid4().hex[:6]
        test_oid = f"ORD-ELIG-TEST-{uid}"
        line_perish = f"LINE-PERISH-{uid}"
        line_normal = f"LINE-NORM-{uid}"
        
        # Order delivered 10 days ago (> 7 days)
        cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, customer_id, order_date, delivery_date, total_amount_inr, net_amount_inr, status, payment_method)
            VALUES (?, 'CUST-IND-001', '2026-11-01 10:00:00', '2026-11-04 12:00:00', 5000.0, 5000.0, 'delivered', 'upi')
        """, (test_oid,))
        
        # Non-returnable line (e.g., perishables, is_returnable=0)
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines 
            (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr, is_returnable, return_window_days)
            VALUES (?, ?, 'PROD-PERISH-001', 'Mangoes', 'perishables', 1, 1200.0, 1200.0, 0, 0)
        """, (line_perish, test_oid))

        # Returnable line but delivered 10 days ago (window expired)
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines 
            (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr, is_returnable, return_window_days)
            VALUES (?, ?, 'PROD-ELEC-002', 'Headphones', 'electronics', 2, 1900.0, 3800.0, 1, 7)
        """, (line_normal, test_oid))
        conn.commit()
        conn.close()

        # 1. Non-returnable category must be rejected
        res_perish = self.client.post("/api/v1/customer/request-return", json={
            "order_id": test_oid,
            "order_line_id": line_perish,
            "customer_id": "CUST-IND-001",
            "quantity": 1,
            "reason": "defective"
        })
        self.assertEqual(res_perish.status_code, 400)
        self.assertIn("non-returnable", res_perish.json()["detail"].lower())

        # 2. Return quantity exceeding purchased quantity must be rejected
        res_excess = self.client.post("/api/v1/customer/request-return", json={
            "order_id": test_oid,
            "order_line_id": line_normal,
            "customer_id": "CUST-IND-001",
            "quantity": 5,  # Only bought 2
            "reason": "defective"
        })
        self.assertEqual(res_excess.status_code, 400)
        self.assertIn("exceeds purchased quantity", res_excess.json()["detail"].lower())

        # 3. Requesting return after 7 days without override must be rejected
        res_late = self.client.post("/api/v1/customer/request-return", json={
            "order_id": test_oid,
            "order_line_id": line_normal,
            "customer_id": "CUST-IND-001",
            "quantity": 1,
            "reason": "defective"
        })
        self.assertEqual(res_late.status_code, 400)
        self.assertIn("expired", res_late.json()["detail"].lower())

    def test_10_refund_math_reconciliation(self):
        """Test refund math reconciles strictly: net_refund == gross_refund - restocking_fee - shipping_fee"""
        import uuid
        conn = get_db()
        cursor = conn.cursor()
        uid = uuid.uuid4().hex[:6]
        test_oid = f"ORD-REFUND-MATH-{uid}"
        test_lid = f"LINE-MATH-{uid}"

        # Unit price: ₹10,000, 10% discount, 18% GST -> Net Line Total: 10000 * 0.9 * 1.18 = ₹10,620
        cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, customer_id, order_date, delivery_date, total_amount_inr, net_amount_inr, status, payment_method)
            VALUES (?, 'CUST-IND-003', '2026-11-12 10:00:00', '2026-11-13 10:00:00', 10620.0, 10620.0, 'delivered', 'upi')
        """, (test_oid,))
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines 
            (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, discount_pct, gst_pct, line_total_inr, is_returnable)
            VALUES (?, ?, 'PROD-ELEC-002', 'Headphones Pro', 'electronics', 1, 10000.0, 10.0, 18.0, 10620.0, 1)
        """, (test_lid, test_oid))
        conn.commit()
        conn.close()

        # Customer raises return (reason: 'changed_mind' -> invokes ₹100 customer shipping fee)
        res_req = self.client.post("/api/v1/customer/request-return", json={
            "order_id": test_oid,
            "order_line_id": test_lid,
            "customer_id": "CUST-IND-003",
            "quantity": 1,
            "reason": "changed_mind"
        })
        self.assertEqual(res_req.status_code, 200)
        rma_id = res_req.json()["request_id"]

        # Operations Manager approves
        res_dec = self.client.post("/api/v1/operations/decide", json={
            "request_id": rma_id,
            "action": "approve"
        })
        self.assertEqual(res_dec.status_code, 200)
        dec_data = res_dec.json()
        gross = dec_data["gross_refund_inr"]
        net = dec_data["net_refund_inr"]

        # Reconcile math: Gross must equal line total (10620.0), Net must equal Gross - 100 (10520.0)
        self.assertEqual(gross, 10620.0)
        self.assertEqual(net, 10520.0)
        self.assertEqual(net, gross - 100.0)

    def test_11_disposition_controls_inventory_movement(self):
        """Test warehouse physical disposition controls inventory: restock increments sellable stock, scrap does not"""
        import uuid
        conn = get_db()
        cursor = conn.cursor()
        uid = uuid.uuid4().hex[:6]
        
        # Check initial stock of PROD-ELEC-001
        cursor.execute("SELECT stock_quantity FROM inventory WHERE product_id = 'PROD-ELEC-001'")
        initial_stock = cursor.fetchone()[0]

        # Create dummy authorization & shipment for PROD-ELEC-001
        test_oid = f"ORD-DISP-{uid}"
        test_lid = f"LINE-DISP-{uid}"
        test_rma = f"RMA-DISP-{uid}"
        test_rl = f"RMAL-DISP-{uid}"
        test_auth = f"AUTH-DISP-{uid}"
        test_ship_restock = f"RTS-DISP-RESTOCK-{uid}"
        test_ship_scrap = f"RTS-DISP-SCRAP-{uid}"

        cursor.execute("""
            INSERT OR REPLACE INTO orders (order_id, customer_id, order_date, delivery_date, total_amount_inr, net_amount_inr, status)
            VALUES (?, 'CUST-IND-001', '2026-11-12 10:00:00', '2026-11-13 10:00:00', 5000.0, 5000.0, 'delivered')
        """, (test_oid,))
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr)
            VALUES (?, ?, 'PROD-ELEC-001', 'Phone', 'electronics', 1, 5000.0, 5000.0)
        """, (test_lid, test_oid))
        cursor.execute("""
            INSERT OR REPLACE INTO return_requests (request_id, customer_id, order_id, request_date, reason, status)
            VALUES (?, 'CUST-IND-001', ?, '2026-11-13 12:00:00', 'defective', 'approved')
        """, (test_rma, test_oid))
        cursor.execute("""
            INSERT OR REPLACE INTO return_lines (line_id, request_id, order_line_id, requested_qty, approved_qty, status)
            VALUES (?, ?, ?, 1, 1, 'approved')
        """, (test_rl, test_rma, test_lid))
        cursor.execute("""
            INSERT OR REPLACE INTO return_authorizations (auth_id, request_id, authorized_by, authorized_at, expiry_date, auth_status)
            VALUES (?, ?, 'ops', '2026-11-13 14:00:00', '2026-11-27', 'active')
        """, (test_auth, test_rma))
        cursor.execute("""
            INSERT OR REPLACE INTO return_shipments (shipment_id, auth_id, carrier, tracking_number, status)
            VALUES (?, ?, 'BlueDart', 'TRK-001', 'shipped')
        """, (test_ship_restock, test_auth))
        conn.commit()
        conn.close()

        # 1. Warehouse inspects and selects 'restock' -> Sellable stock MUST increment by 1
        res_restock = self.client.post("/api/v1/warehouse/inspect", json={
            "shipment_id": test_ship_restock,
            "quality_grade": "Grade A",
            "overall_condition": "excellent",
            "recommended_action": "restock",
            "checklist_passed": True
        })
        self.assertEqual(res_restock.status_code, 200)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT stock_quantity FROM inventory WHERE product_id = 'PROD-ELEC-001'")
        stock_after_restock = cursor.fetchone()[0]
        self.assertEqual(stock_after_restock, initial_stock + 1)

        # 2. Warehouse inspects another shipment and selects 'scrap' -> Sellable stock must NOT increment
        cursor.execute("""
            INSERT OR REPLACE INTO return_shipments (shipment_id, auth_id, carrier, tracking_number, status)
            VALUES (?, ?, 'Delhivery', 'TRK-002', 'shipped')
        """, (test_ship_scrap, test_auth))
        conn.commit()
        conn.close()

        res_scrap = self.client.post("/api/v1/warehouse/inspect", json={
            "shipment_id": test_ship_scrap,
            "quality_grade": "Grade D",
            "overall_condition": "unusable",
            "recommended_action": "scrap",
            "checklist_passed": False
        })
        self.assertEqual(res_scrap.status_code, 200)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT stock_quantity FROM inventory WHERE product_id = 'PROD-ELEC-001'")
        stock_after_scrap = cursor.fetchone()[0]
        # Sellable stock remained the same (NOT incremented)
        self.assertEqual(stock_after_scrap, stock_after_restock)
        conn.close()

    def test_12_duplicate_payouts_blocked(self):
        """Test duplicate payout prevention: second approval attempt is blocked (HTTP 400) and does not double credit wallet"""
        import uuid
        conn = get_db()
        cursor = conn.cursor()
        uid = uuid.uuid4().hex[:6]
        test_oid = f"ORD-DUP-PAY-{uid}"
        test_lid = f"LINE-DUP-{uid}"
        test_rma = f"RMA-DUP-{uid}"
        test_rl = f"RMAL-DUP-{uid}"

        cursor.execute("SELECT wallet_balance_inr FROM customers WHERE customer_id = 'CUST-IND-001'")
        init_wallet = cursor.fetchone()[0]

        cursor.execute("""
            INSERT OR REPLACE INTO orders (order_id, customer_id, order_date, delivery_date, total_amount_inr, net_amount_inr, status)
            VALUES (?, 'CUST-IND-001', '2026-11-12 10:00:00', '2026-11-13 10:00:00', 4000.0, 4000.0, 'delivered')
        """, (test_oid,))
        cursor.execute("""
            INSERT OR REPLACE INTO order_lines (line_id, order_id, product_id, product_name, category, quantity, unit_price_inr, line_total_inr, is_returnable)
            VALUES (?, ?, 'PROD-ELEC-001', 'Phone', 'electronics', 1, 4000.0, 4000.0, 1)
        """, (test_lid, test_oid))
        cursor.execute("""
            INSERT OR REPLACE INTO return_requests (request_id, customer_id, order_id, request_date, reason, status, days_since_delivery)
            VALUES (?, 'CUST-IND-001', ?, '2026-11-13 12:00:00', 'defective', 'pending', 1)
        """, (test_rma, test_oid))
        cursor.execute("""
            INSERT OR REPLACE INTO return_lines (line_id, request_id, order_line_id, requested_qty, approved_qty, status)
            VALUES (?, ?, ?, 1, NULL, 'pending')
        """, (test_rl, test_rma, test_lid))
        conn.commit()
        conn.close()

        # 1. First approval -> succeeds and issues refund
        res1 = self.client.post("/api/v1/operations/decide", json={
            "request_id": test_rma,
            "action": "approve"
        })
        self.assertEqual(res1.status_code, 200)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT wallet_balance_inr FROM customers WHERE customer_id = 'CUST-IND-001'")
        wallet_after_first = cursor.fetchone()[0]
        self.assertEqual(wallet_after_first, init_wallet + 4000.0)
        conn.close()

        # 2. Second approval on same request -> MUST BE BLOCKED (HTTP 400)
        res2 = self.client.post("/api/v1/operations/decide", json={
            "request_id": test_rma,
            "action": "approve"
        })
        self.assertEqual(res2.status_code, 400)
        self.assertIn("duplicate payout blocked", res2.json()["detail"].lower())

        # Customer wallet was NOT double credited
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT wallet_balance_inr FROM customers WHERE customer_id = 'CUST-IND-001'")
        wallet_after_second = cursor.fetchone()[0]
        self.assertEqual(wallet_after_second, wallet_after_first)

        # Anomaly was logged in anomaly_records
        cursor.execute("SELECT COUNT(*) FROM anomaly_records WHERE entity_type = 'refund' AND anomaly_type = 'duplicate_refund'")
        self.assertGreater(cursor.fetchone()[0], 0)
        conn.close()


if __name__ == "__main__":
    unittest.main()
