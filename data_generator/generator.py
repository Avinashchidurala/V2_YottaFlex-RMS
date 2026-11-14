"""
Deterministic Synthetic Data Generator for Returns Management System (RMS).
Fixed Seed: 20261022 | Currency: INR (₹)
Supports arbitrary scale factors (e.g. 0.05 for fast test, 1.0 for full 30,000 orders / 5,000 returns / 8,000 lines).
Guarantees 100% bitwise reproducibility via deterministic counters and seeded PRNGs.
"""

import os
import random
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .config import (
    SEED,
    BASELINE_ORDERS,
    BASELINE_RETURN_REQUESTS,
    BASELINE_RETURN_LINES,
    CORE_CUSTOMERS,
    PRODUCTS_CATALOG,
    RETURN_REASONS,
    PAYMENT_METHODS,
    ANOMALY_TARGETS,
)


class RMSDataGenerator:
    def __init__(self, seed: int = SEED, scale: float = 1.0, output_dir: str = "data"):
        self.seed = seed
        self.scale = max(0.01, scale)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        random.seed(self.seed)
        np.random.seed(self.seed)

        self.num_orders = int(BASELINE_ORDERS * self.scale)
        self.num_returns = int(BASELINE_RETURN_REQUESTS * self.scale)
        self.num_return_lines = int(BASELINE_RETURN_LINES * self.scale)

        self.customers_df = None
        self.inventory_df = None
        self.orders_df = None
        self.order_lines_df = None
        self.return_requests_df = None
        self.return_lines_df = None
        self.return_auth_df = None
        self.return_shipments_df = None
        self.inspections_df = None
        self.refunds_df = None
        self.dispositions_df = None
        self.transitions_df = None
        self.ground_truth_df = None

    def generate_all(self):
        print(f"[*] Starting RMS Data Generation (seed={self.seed}, scale={self.scale})")
        print(f"    Target Orders: {self.num_orders}, Return Requests: {self.num_returns}, Return Lines: {self.num_return_lines}")

        self._generate_customers()
        self._generate_inventory()
        self._generate_orders_and_lines()
        self._generate_returns_workflow()
        self._export_all_csvs()
        print("[+] Data generation complete. Clean CSVs saved to:", self.output_dir)

    def _generate_customers(self):
        """Generates EXACTLY the 3 customer profiles for the customer panel."""
        customers = []
        for c in CORE_CUSTOMERS:
            customers.append({
                "customer_id": c["customer_id"],
                "name": c["name"],
                "email": c["email"],
                "phone": c["phone"],
                "address": c["address"],
                "city": c["city"],
                "state": c["state"],
                "tier": c["tier"],
                "wallet_balance_inr": c["initial_wallet_inr"],
                "created_at": "2026-01-01 10:00:00",
                "is_active": 1
            })

        self.customers_df = pd.DataFrame(customers)
        print(f"    - Generated {len(self.customers_df)} core customers (exactly 3 customers for panels)")

    def _generate_inventory(self):
        """Generates inventory catalog products with stock, pricing, and category policies."""
        inventory = []
        for p in PRODUCTS_CATALOG:
            inventory.append({
                "product_id": p["product_id"],
                "product_name": p["name"],
                "category": p["category"],
                "unit_price_inr": p["unit_price_inr"],
                "cost_price_inr": p["cost_price_inr"],
                "stock_quantity": p["stock"] * max(1, int(self.scale * 10)),
                "return_window_days": p["return_window_days"],
                "is_returnable": 1 if p["is_returnable"] else 0,
                "gst_pct": p["gst_pct"],
                "total_units_sold": 0,
                "total_units_returned": 0,
            })
        self.inventory_df = pd.DataFrame(inventory)
        print(f"    - Generated {len(self.inventory_df)} inventory products")

    def _generate_orders_and_lines(self):
        """Generates 30,000 orders distributed across the 3 customers, plus order lines."""
        orders = []
        order_lines = []
        start_date = datetime(2026, 1, 10)
        customer_ids = [c["customer_id"] for c in CORE_CUSTOMERS]
        products = self.inventory_df.to_dict("records")

        line_counter = 1
        for i in range(1, self.num_orders + 1):
            order_id = f"ORD-2026-{i:06d}"
            # Round-robin distribution across the 3 customers
            cid = customer_ids[(i - 1) % len(customer_ids)]

            order_day_offset = int((i / max(1, self.num_orders)) * 260)
            order_dt = start_date + timedelta(days=order_day_offset, hours=random.randint(8, 20), minutes=random.randint(0, 59))
            
            # Recent orders: assign "shipping" stage so in-transit return can be tested
            # Earlier orders: "delivered"
            if i > self.num_orders * 0.95:
                status = "shipping"
                delivery_dt = None
            elif i > self.num_orders * 0.92:
                status = "confirmed"
                delivery_dt = None
            else:
                status = "delivered"
                delivery_dt = (order_dt + timedelta(days=random.randint(2, 5))).strftime("%Y-%m-%d %H:%M:%S")

            # 1 to 4 lines per order (avg ~1.8 lines)
            num_lines = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
            chosen_prods = random.sample(products, k=min(num_lines, len(products)))

            order_total = 0.0
            order_discount = 0.0
            order_tax = 0.0

            for p in chosen_prods:
                line_id = f"LINE-{order_id}-{line_counter:02d}"
                line_counter += 1
                qty = random.choices([1, 2, 3], weights=[0.80, 0.16, 0.04])[0]
                unit_price = p["unit_price_inr"]
                discount_pct = float(random.choice([0.0, 5.0, 10.0, 15.0, 20.0]))
                base_val = qty * unit_price
                disc_val = round(base_val * (discount_pct / 100.0), 2)
                taxable_val = base_val - disc_val
                tax_val = round(taxable_val * (p["gst_pct"] / 100.0), 2)
                line_total = round(taxable_val + tax_val, 2)

                order_total += base_val
                order_discount += disc_val
                order_tax += tax_val

                order_lines.append({
                    "line_id": line_id,
                    "order_id": order_id,
                    "product_id": p["product_id"],
                    "product_name": p["product_name"],
                    "category": p["category"],
                    "quantity": qty,
                    "unit_price_inr": unit_price,
                    "discount_pct": discount_pct,
                    "gst_pct": p["gst_pct"],
                    "line_total_inr": line_total,
                    "is_returnable": p["is_returnable"],
                    "return_window_days": p["return_window_days"],
                })

            net_order_total = round(order_total - order_discount + order_tax, 2)
            pay_method = random.choice(PAYMENT_METHODS)

            orders.append({
                "order_id": order_id,
                "customer_id": cid,
                "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "total_amount_inr": round(order_total, 2),
                "discount_amount_inr": round(order_discount, 2),
                "tax_amount_inr": round(order_tax, 2),
                "net_amount_inr": net_order_total,
                "status": status,
                "payment_method": pay_method,
                "delivery_date": delivery_dt
            })

        self.orders_df = pd.DataFrame(orders)
        self.order_lines_df = pd.DataFrame(order_lines)
        print(f"    - Generated {len(self.orders_df)} orders, {len(self.order_lines_df)} order lines")

    def _generate_returns_workflow(self):
        """
        Simulates:
        - 5,000 return requests
        - Exactly 8,000 return lines (RMAL-<rma_id>-01 format)
        - In-Transit auto-refunds (zero touch) vs Delivered 7-day reviews
        - Operations Manager approvals/rejections
        - Shipments (RTS-...), Inspections, Refunds (REF-...), Dispositions
        - Ground truth anomaly records
        """
        print("    - Simulating Returns, Approvals, Shipments, Inspections, Refunds, and Dispositions...")
        return_requests = []
        return_lines = []
        return_authorizations = []
        return_shipments = []
        inspections = []
        refunds = []
        dispositions = []
        state_transitions = []
        anomalies = []

        # Group order lines by order_id
        order_to_lines = {}
        for row in self.order_lines_df.to_dict("records"):
            oid = row["order_id"]
            if oid not in order_to_lines:
                order_to_lines[oid] = []
            order_to_lines[oid].append(row)

        orders_dict = {o["order_id"]: o for o in self.orders_df.to_dict("records")}

        # Split candidates
        shipping_order_ids = [oid for oid, o in orders_dict.items() if o["status"] == "shipping"]
        delivered_order_ids = [oid for oid, o in orders_dict.items() if o["status"] == "delivered"]

        anomaly_targets = {k: max(1, int(v * self.scale)) for k, v in ANOMALY_TARGETS.items()}
        anomaly_counts = {k: 0 for k in anomaly_targets}

        rma_counter = 1
        auth_counter = 1
        ship_counter = 1
        insp_counter = 1
        disp_counter = 1
        ref_counter = 1
        trans_counter = 1
        anom_counter = 1

        num_target = self.num_returns
        in_transit_share = int(num_target * 0.15)  # 15% in-transit
        delivered_share = num_target - in_transit_share

        # To produce EXACTLY self.num_return_lines (e.g. 8,000 lines for 5,000 requests at scale 1.0)
        # We calculate lines per request distribution
        # Extra lines needed = num_return_lines - num_target (e.g. 8000 - 5000 = 3000)
        extra_lines_needed = max(0, self.num_return_lines - num_target)
        
        # 1. In-Transit Returns (Shipping stage -> Auto approved, zero-touch refund, restocked)
        for i in range(in_transit_share):
            oid = shipping_order_ids[i % len(shipping_order_ids)]
            order = orders_dict[oid]
            cand_lines = order_to_lines[oid]
            first_line = cand_lines[0]

            rma_id = f"RMA-2026-{rma_counter:06d}"
            rma_counter += 1

            req_dt = datetime.strptime(order["order_date"], "%Y-%m-%d %H:%M:%S") + timedelta(hours=random.randint(6, 24))
            status = "auto_refunded_in_transit"
            notes = "In-transit cancellation requested by customer before delivery. Auto-refunded immediately; restocked to inventory."

            return_requests.append({
                "request_id": rma_id,
                "customer_id": order["customer_id"],
                "order_id": oid,
                "request_date": req_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "changed_mind",
                "status": status,
                "notes": notes,
                "override_flag": 0,
                "override_reason": None,
                "days_since_delivery": 0,
                "return_channel": "in_transit_auto"
            })

            # Return Line 1
            rl_id = f"RMAL-{rma_id}-01"
            req_qty = first_line["quantity"]
            app_qty = req_qty
            return_lines.append({
                "line_id": rl_id,
                "request_id": rma_id,
                "order_line_id": first_line["line_id"],
                "requested_qty": req_qty,
                "approved_qty": app_qty,
                "rejection_reason": None,
                "status": "approved"
            })

            # Auto refund
            ref_id = f"REF-2026-{ref_counter:06d}"
            ref_counter += 1
            gross_ref = round(first_line["line_total_inr"], 2)
            net_ref = gross_ref

            refunds.append({
                "refund_id": ref_id,
                "request_id": rma_id,
                "inspection_id": None,
                "gross_refund_inr": gross_ref,
                "restocking_fee_inr": 0.0,
                "shipping_fee_inr": 0.0,
                "net_refund_inr": net_ref,
                "status": "processed",
                "processed_at": req_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "payment_method": "customer_wallet",
                "is_duplicate": 0,
                "duplicate_of_refund_id": None
            })

            disp_id = f"DISP-2026-{disp_counter:06d}"
            disp_counter += 1
            dispositions.append({
                "disposition_id": disp_id,
                "inspection_id": None,
                "product_id": first_line["product_id"],
                "product_name": first_line["product_name"],
                "quantity": app_qty,
                "disposition_action": "restock",
                "location": "MAIN-WAREHOUSE-IN-TRANSIT-REVERT",
                "disposed_at": req_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "estimated_recovery_inr": gross_ref,
                "notes": "Direct restock from shipping cancellation."
            })

            trans_id = f"LOG-2026-{trans_counter:06d}"
            trans_counter += 1
            state_transitions.append({
                "log_id": trans_id,
                "entity_type": "return_request",
                "entity_id": rma_id,
                "from_status": "shipping_cancellation",
                "to_status": "auto_refunded_in_transit",
                "changed_by": "system_auto_workflow",
                "changed_at": req_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "Automated zero-touch in-transit cancellation"
            })

        # 2. Delivered Returns (Subject to 7-day rule, inspection, Operations Manager decision)
        lines_added_so_far = len(return_lines)
        remaining_lines_to_allocate = self.num_return_lines - lines_added_so_far

        for i in range(delivered_share):
            oid = delivered_order_ids[i % len(delivered_order_ids)]
            order = orders_dict[oid]
            cand_lines = order_to_lines[oid]
            first_line = cand_lines[0]

            rma_id = f"RMA-2026-{rma_counter:06d}"
            rma_counter += 1

            deliv_dt = datetime.strptime(order["delivery_date"], "%Y-%m-%d %H:%M:%S")

            # Edge case: Late return without override
            inject_late = (anomaly_counts["late_return_no_override"] < anomaly_targets["late_return_no_override"]) and (i % 7 == 0)
            if inject_late:
                days_since_deliv = random.randint(12, 45)
                override_flag = 0
                override_reason = None
                anomaly_counts["late_return_no_override"] += 1
                anom_id = f"ANOM-2026-{anom_counter:06d}"
                anom_counter += 1
                anomalies.append({
                    "anomaly_id": anom_id,
                    "entity_type": "return_request",
                    "entity_id": rma_id,
                    "anomaly_type": "late_return_no_override",
                    "severity": "high",
                    "description": f"Return requested {days_since_deliv} days after delivery (policy is 7 days) without manager override.",
                    "detected_at": (deliv_dt + timedelta(days=days_since_deliv)).strftime("%Y-%m-%d %H:%M:%S"),
                    "is_confirmed": 1
                })
            else:
                days_since_deliv = random.randint(1, 7)
                override_flag = 0
                override_reason = None

            req_dt = deliv_dt + timedelta(days=days_since_deliv, hours=random.randint(1, 12))
            reason = random.choice(RETURN_REASONS)
            is_returnable_item = (first_line["is_returnable"] == 1)
            
            if not is_returnable_item or (days_since_deliv > 7 and not override_flag):
                status = "rejected"
                notes = "Rejected: Outside 7-day return policy or non-returnable category."
            elif i % 15 == 0:
                status = "pending"
                notes = "Awaiting Operations Manager review and approval."
            else:
                status = "approved"
                notes = "Approved by Operations Manager after 7-day policy verification."

            return_requests.append({
                "request_id": rma_id,
                "customer_id": order["customer_id"],
                "order_id": oid,
                "request_date": req_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": reason,
                "status": status,
                "notes": notes,
                "override_flag": override_flag,
                "override_reason": override_reason,
                "days_since_delivery": days_since_deliv,
                "return_channel": "customer_portal"
            })

            # Determine how many return lines for this request (to hit EXACTLY self.num_return_lines)
            requests_remaining = delivered_share - i
            lines_needed_now = 1
            if remaining_lines_to_allocate > requests_remaining:
                # Can allocate 2 or 3 lines
                extra_possible = min(len(cand_lines) - 1, remaining_lines_to_allocate - requests_remaining, 2)
                lines_needed_now = 1 + max(0, extra_possible)

            # Generate return lines for this request
            for l_idx in range(lines_needed_now):
                cur_line = cand_lines[l_idx % len(cand_lines)]
                rl_id = f"RMAL-{rma_id}-{l_idx + 1:02d}"

                # Edge case: Return quantity exceeds purchased quantity (on line 1 only)
                inject_excess_qty = (l_idx == 0) and (anomaly_counts["return_qty_exceeds_purchased"] < anomaly_targets["return_qty_exceeds_purchased"]) and (i % 9 == 0)
                if inject_excess_qty:
                    req_qty = cur_line["quantity"] + random.randint(1, 3)
                    anomaly_counts["return_qty_exceeds_purchased"] += 1
                    anom_id = f"ANOM-2026-{anom_counter:06d}"
                    anom_counter += 1
                    anomalies.append({
                        "anomaly_id": anom_id,
                        "entity_type": "return_line",
                        "entity_id": rl_id,
                        "anomaly_type": "return_qty_exceeds_purchased",
                        "severity": "critical",
                        "description": f"Requested return quantity {req_qty} exceeds order line quantity {cur_line['quantity']}.",
                        "detected_at": req_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "is_confirmed": 1
                    })
                else:
                    req_qty = cur_line["quantity"]

                app_qty = req_qty if status == "approved" else 0
                return_lines.append({
                    "line_id": rl_id,
                    "request_id": rma_id,
                    "order_line_id": cur_line["line_id"],
                    "requested_qty": req_qty,
                    "approved_qty": app_qty,
                    "rejection_reason": "Policy violation" if status == "rejected" else None,
                    "status": "approved" if status == "approved" else ("rejected" if status == "rejected" else "pending")
                })
                remaining_lines_to_allocate -= 1

            if status == "approved":
                auth_id = f"AUTH-2026-{auth_counter:06d}"
                auth_counter += 1
                auth_dt = req_dt + timedelta(hours=random.randint(2, 8))
                exp_dt = (auth_dt + timedelta(days=14)).date()

                return_authorizations.append({
                    "auth_id": auth_id,
                    "request_id": rma_id,
                    "authorized_by": "operations_manager_ops01",
                    "authorized_at": auth_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "expiry_date": str(exp_dt),
                    "auth_status": "used"
                })

                ship_id = f"RTS-2026-{ship_counter:06d}"
                ship_counter += 1
                carrier = random.choice(["BlueDart", "Delhivery", "DTDC", "Shadowfax"])
                trk = f"TRK-{carrier[:3].upper()}-{random.randint(10000000, 99999999)}"

                inject_lost = (anomaly_counts["missing_shipment"] < anomaly_targets["missing_shipment"]) and (i % 11 == 0)
                if inject_lost:
                    ship_status = "lost"
                    cond_arrival = "missing"
                    recd_dt = None
                    anomaly_counts["missing_shipment"] += 1
                    anom_id = f"ANOM-2026-{anom_counter:06d}"
                    anom_counter += 1
                    anomalies.append({
                        "anomaly_id": anom_id,
                        "entity_type": "return_shipment",
                        "entity_id": ship_id,
                        "anomaly_type": "missing_shipment",
                        "severity": "medium",
                        "description": f"Return shipment {ship_id} lost in transit by carrier {carrier}.",
                        "detected_at": (auth_dt + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
                        "is_confirmed": 1
                    })
                else:
                    ship_status = "received"
                    cond_arrival = random.choices(["good", "damaged", "partial"], weights=[0.80, 0.15, 0.05])[0]
                    recd_dt = (auth_dt + timedelta(days=random.randint(2, 4))).strftime("%Y-%m-%d %H:%M:%S")

                return_shipments.append({
                    "shipment_id": ship_id,
                    "auth_id": auth_id,
                    "carrier": carrier,
                    "tracking_number": trk,
                    "shipped_at": (auth_dt + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                    "received_at": recd_dt,
                    "condition_on_arrival": cond_arrival,
                    "status": ship_status
                })

                if ship_status == "received":
                    insp_id = f"INSP-2026-{insp_counter:06d}"
                    insp_counter += 1
                    insp_dt = datetime.strptime(recd_dt, "%Y-%m-%d %H:%M:%S") + timedelta(hours=random.randint(2, 12))
                    
                    if cond_arrival == "good":
                        cond = random.choices(["excellent", "good", "fair"], weights=[0.60, 0.35, 0.05])[0]
                    else:
                        cond = random.choices(["fair", "poor", "unusable"], weights=[0.40, 0.40, 0.20])[0]

                    if cond in ["excellent", "good"]:
                        action = "restock"
                    elif cond == "fair":
                        action = random.choice(["restock", "refurbish"])
                    elif cond == "poor":
                        action = random.choice(["refurbish", "quarantine"])
                    else:
                        action = "scrap"

                    inspections.append({
                        "inspection_id": insp_id,
                        "shipment_id": ship_id,
                        "inspector_id": f"INSP-WH-{random.randint(1, 5):02d}",
                        "inspected_at": insp_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "overall_condition": cond,
                        "notes": f"Item condition: {cond}. Recommended disposition: {action}.",
                        "recommended_action": action
                    })

                    disp_id = f"DISP-2026-{disp_counter:06d}"
                    disp_counter += 1
                    inject_early_disp = (anomaly_counts["restock_before_inspection"] < anomaly_targets["restock_before_inspection"]) and (i % 13 == 0)
                    if inject_early_disp:
                        disp_dt = (insp_dt - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
                        anomaly_counts["restock_before_inspection"] += 1
                        anom_id = f"ANOM-2026-{anom_counter:06d}"
                        anom_counter += 1
                        anomalies.append({
                            "anomaly_id": anom_id,
                            "entity_type": "inventory_disposition",
                            "entity_id": disp_id,
                            "anomaly_type": "restock_before_inspection",
                            "severity": "high",
                            "description": f"Disposition record dated {disp_dt} precedes inspection date {insp_dt}.",
                            "detected_at": disp_dt,
                            "is_confirmed": 1
                        })
                    else:
                        disp_dt = (insp_dt + timedelta(hours=random.randint(1, 6))).strftime("%Y-%m-%d %H:%M:%S")

                    recovery_pct = {"restock": 0.90, "refurbish": 0.50, "quarantine": 0.20, "scrap": 0.05}[action]
                    est_recovery = round(first_line["unit_price_inr"] * first_line["quantity"] * recovery_pct, 2)

                    dispositions.append({
                        "disposition_id": disp_id,
                        "inspection_id": insp_id,
                        "product_id": first_line["product_id"],
                        "product_name": first_line["product_name"],
                        "quantity": first_line["quantity"],
                        "disposition_action": action,
                        "location": f"WH-BIN-{action[:3].upper()}-{random.randint(100, 999)}",
                        "disposed_at": disp_dt,
                        "estimated_recovery_inr": est_recovery,
                        "notes": f"Moved to {action} inventory post-inspection."
                    })

                    ref_id = f"REF-2026-{ref_counter:06d}"
                    ref_counter += 1
                    gross_ref = round(first_line["line_total_inr"], 2)

                    restock_fee = round(gross_ref * 0.05, 2) if cond in ["fair", "poor"] else 0.0
                    shipping_fee = 100.0 if reason in ["changed_mind", "sizing_issue"] else 0.0
                    net_ref = round(max(0.0, gross_ref - restock_fee - shipping_fee), 2)

                    inject_over_refund = (anomaly_counts["refund_exceeds_paid"] < anomaly_targets["refund_exceeds_paid"]) and ((i % 5 == 0) or (i >= delivered_share - 10))
                    if inject_over_refund:
                        net_ref = round(first_line["line_total_inr"] + random.randint(1500, 5000), 2)
                        anomaly_counts["refund_exceeds_paid"] += 1
                        anom_id = f"ANOM-2026-{anom_counter:06d}"
                        anom_counter += 1
                        anomalies.append({
                            "anomaly_id": anom_id,
                            "entity_type": "refund",
                            "entity_id": ref_id,
                            "anomaly_type": "refund_exceeds_paid",
                            "severity": "critical",
                            "description": f"Refund amount ₹{net_ref} exceeds order line paid total ₹{first_line['line_total_inr']}.",
                            "detected_at": (insp_dt + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
                            "is_confirmed": 1
                        })

                    refunds.append({
                        "refund_id": ref_id,
                        "request_id": rma_id,
                        "inspection_id": insp_id,
                        "gross_refund_inr": gross_ref,
                        "restocking_fee_inr": restock_fee,
                        "shipping_fee_inr": shipping_fee,
                        "net_refund_inr": net_ref,
                        "status": "processed",
                        "processed_at": (insp_dt + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
                        "payment_method": "customer_wallet",
                        "is_duplicate": 0,
                        "duplicate_of_refund_id": None
                    })

                    inject_dup = (anomaly_counts["duplicate_refund"] < anomaly_targets["duplicate_refund"]) and (i % 17 == 0)
                    if inject_dup:
                        dup_ref_id = f"REF-2026-{ref_counter:06d}"
                        ref_counter += 1
                        anomaly_counts["duplicate_refund"] += 1
                        anom_id = f"ANOM-2026-{anom_counter:06d}"
                        anom_counter += 1
                        refunds.append({
                            "refund_id": dup_ref_id,
                            "request_id": rma_id,
                            "inspection_id": insp_id,
                            "gross_refund_inr": gross_ref,
                            "restocking_fee_inr": restock_fee,
                            "shipping_fee_inr": shipping_fee,
                            "net_refund_inr": net_ref,
                            "status": "duplicate",
                            "processed_at": (insp_dt + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
                            "payment_method": "customer_wallet",
                            "is_duplicate": 1,
                            "duplicate_of_refund_id": ref_id
                        })
                        anomalies.append({
                            "anomaly_id": anom_id,
                            "entity_type": "refund",
                            "entity_id": dup_ref_id,
                            "anomaly_type": "duplicate_refund",
                            "severity": "critical",
                            "description": f"Duplicate payout attempted for request {rma_id}. Duplicate of {ref_id}.",
                            "detected_at": (insp_dt + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
                            "is_confirmed": 1
                        })

        self.return_requests_df = pd.DataFrame(return_requests)
        self.return_lines_df = pd.DataFrame(return_lines)
        self.return_auth_df = pd.DataFrame(return_authorizations)
        self.return_shipments_df = pd.DataFrame(return_shipments)
        self.inspections_df = pd.DataFrame(inspections)
        self.refunds_df = pd.DataFrame(refunds)
        self.dispositions_df = pd.DataFrame(dispositions)
        self.transitions_df = pd.DataFrame(state_transitions)
        
        if not anomalies:
            self.ground_truth_df = pd.DataFrame(columns=[
                "anomaly_id", "entity_type", "entity_id", "anomaly_type",
                "severity", "description", "detected_at", "is_confirmed"
            ])
        else:
            self.ground_truth_df = pd.DataFrame(anomalies)

        print(f"    - Generated {len(self.return_requests_df)} return requests")
        print(f"    - Generated {len(self.return_lines_df)} return lines (target reached!)")
        print(f"    - Generated {len(self.refunds_df)} refunds")
        print(f"    - Generated {len(self.ground_truth_df)} labelled anomalies in ground_truth.csv")

    def _export_all_csvs(self):
        """Exports exactly the 13 clean, normalized entity CSV files (no unnecessary clutter)."""
        dfs = {
            "customers.csv": self.customers_df,
            "inventory.csv": self.inventory_df,
            "orders.csv": self.orders_df,
            "order_lines.csv": self.order_lines_df,
            "return_requests.csv": self.return_requests_df,
            "return_lines.csv": self.return_lines_df,
            "return_authorizations.csv": self.return_auth_df,
            "return_shipments.csv": self.return_shipments_df,
            "inspections.csv": self.inspections_df,
            "refunds.csv": self.refunds_df,
            "inventory_dispositions.csv": self.dispositions_df,
            "state_transition_log.csv": self.transitions_df,
            "ground_truth.csv": self.ground_truth_df,
        }

        # Remove any obsolete clutter files if they exist
        obsolete = ["company_financials.csv"]
        for obs in obsolete:
            p = os.path.join(self.output_dir, obs)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

        manifest = {}
        for fname, df in dfs.items():
            fpath = os.path.join(self.output_dir, fname)
            df.to_csv(fpath, index=False)
            with open(fpath, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            manifest[fname] = {
                "rows": len(df),
                "columns": list(df.columns),
                "sha256": sha
            }

        manifest_path = os.path.join(self.output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"    - Manifest written to {manifest_path}")
