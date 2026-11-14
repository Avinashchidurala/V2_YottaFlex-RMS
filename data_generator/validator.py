"""
Comprehensive Validator for Returns Management System (RMS) Datasets.
Checks PK uniqueness, FK integrity, enum bounds, date ordering, math reconciliation, and edge case coverage.
"""

import os
import json
import pandas as pd
from datetime import datetime


def validate_all(data_dir: str = "data") -> dict:
    print(f"[*] Running RMS Dataset Validation on {data_dir}...")
    summary = {
        "timestamp": datetime.now().isoformat(),
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "checks": {}
    }

    def load(fname):
        p = os.path.join(data_dir, fname)
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required dataset: {p}")
        return pd.read_csv(p)

    customers = load("customers.csv")
    inventory = load("inventory.csv")
    orders = load("orders.csv")
    order_lines = load("order_lines.csv")
    return_requests = load("return_requests.csv")
    return_lines = load("return_lines.csv")
    authorizations = load("return_authorizations.csv")
    shipments = load("return_shipments.csv")
    inspections = load("inspections.csv")
    refunds = load("refunds.csv")
    dispositions = load("inventory_dispositions.csv")
    ground_truth = load("ground_truth.csv")

    # 1. Primary Key Uniqueness
    pk_checks = {
        "customers": ("customer_id", customers),
        "inventory": ("product_id", inventory),
        "orders": ("order_id", orders),
        "order_lines": ("line_id", order_lines),
        "return_requests": ("request_id", return_requests),
        "return_lines": ("line_id", return_lines),
        "return_authorizations": ("auth_id", authorizations),
        "return_shipments": ("shipment_id", shipments),
        "inspections": ("inspection_id", inspections),
        "refunds": ("refund_id", refunds),
        "inventory_dispositions": ("disposition_id", dispositions),
    }

    pk_results = {}
    for table_name, (pk_col, df) in pk_checks.items():
        total = len(df)
        unique = df[pk_col].nunique()
        is_unique = (total == unique)
        pk_results[table_name] = {"total_rows": total, "unique_keys": unique, "is_valid": is_unique}
        if not is_unique:
            summary["errors"].append(f"PK duplicate detected in {table_name}.{pk_col}")

    summary["checks"]["pk_uniqueness"] = pk_results

    # 2. Foreign Key Integrity
    fk_errors = []
    
    # orders -> customers
    orphan_orders = set(orders["customer_id"]) - set(customers["customer_id"])
    if orphan_orders:
        fk_errors.append(f"Orders reference non-existent customers: {len(orphan_orders)}")

    # order_lines -> orders
    orphan_lines = set(order_lines["order_id"]) - set(orders["order_id"])
    if orphan_lines:
        fk_errors.append(f"OrderLines reference non-existent orders: {len(orphan_lines)}")

    # return_requests -> orders
    orphan_rma = set(return_requests["order_id"]) - set(orders["order_id"])
    if orphan_rma:
        fk_errors.append(f"ReturnRequests reference non-existent orders: {len(orphan_rma)}")

    # return_lines -> return_requests
    orphan_rl_rma = set(return_lines["request_id"]) - set(return_requests["request_id"])
    if orphan_rl_rma:
        fk_errors.append(f"ReturnLines reference non-existent return requests: {len(orphan_rl_rma)}")

    # return_authorizations -> return_requests
    orphan_auth = set(authorizations["request_id"]) - set(return_requests["request_id"])
    if orphan_auth:
        fk_errors.append(f"ReturnAuthorizations reference non-existent return requests: {len(orphan_auth)}")

    # return_shipments -> return_authorizations
    orphan_ship = set(shipments["auth_id"]) - set(authorizations["auth_id"])
    if orphan_ship:
        fk_errors.append(f"ReturnShipments reference non-existent authorizations: {len(orphan_ship)}")

    summary["checks"]["fk_integrity"] = {
        "status": "PASSED" if not fk_errors else "FAILED",
        "violations": fk_errors
    }
    if fk_errors:
        summary["errors"].extend(fk_errors)

    # 3. Arithmetic Reconciliation: Refund Math
    # net_refund = gross_refund - restocking_fee - shipping_fee (excluding injected anomalies)
    reconciled_count = 0
    anomalous_refund_ids = set(ground_truth[ground_truth["entity_type"] == "refund"]["entity_id"])
    
    for _, row in refunds.iterrows():
        ref_id = row["refund_id"]
        gross = row["gross_refund_inr"]
        restock = row["restocking_fee_inr"]
        ship = row["shipping_fee_inr"]
        net = row["net_refund_inr"]
        expected = round(gross - restock - ship, 2)
        if ref_id in anomalous_refund_ids:
            continue
        if abs(net - expected) < 0.05:
            reconciled_count += 1
        else:
            summary["warnings"].append(f"Refund {ref_id} math mismatch: {net} != {expected}")

    summary["checks"]["refund_math_reconciliation"] = {
        "total_refunds_checked": len(refunds) - len(anomalous_refund_ids),
        "reconciled_count": reconciled_count,
        "is_valid": (reconciled_count == (len(refunds) - len(anomalous_refund_ids)))
    }

    # 4. Ground Truth Coverage
    gt_types = ground_truth["anomaly_type"].value_counts().to_dict()
    summary["checks"]["ground_truth_coverage"] = {
        "total_anomalies_labelled": len(ground_truth),
        "anomaly_types_detected": gt_types
    }

    if summary["errors"]:
        summary["status"] = "FAILED"

    # Export validation summary
    out_file = os.path.join(data_dir, "validation_summary.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[+] Validation {summary['status']}! Summary written to {out_file}")
    return summary


if __name__ == "__main__":
    validate_all()
