"""
Generator & Validation Test Suite for Returns Management System (RMS).
Validates:
- Deterministic reproducibility with fixed seed 20261022
- Primary key uniqueness across all 12 tables
- Foreign key integrity
- Arithmetic reconciliation of refund amounts
- Negative scenarios / edge cases isolated in ground_truth.csv
"""

import os
import pytest
import pandas as pd
from data_generator.generator import RMSDataGenerator
from data_generator.validator import validate_all


def test_generator_small_scale():
    test_dir = "data_test_pytest"
    gen = RMSDataGenerator(seed=20261022, scale=0.01, output_dir=test_dir)
    gen.generate_all()

    # Verify all expected CSV files were generated
    expected_files = [
        "customers.csv", "inventory.csv", "orders.csv", "order_lines.csv",
        "return_requests.csv", "return_lines.csv", "return_authorizations.csv",
        "return_shipments.csv", "inspections.csv", "refunds.csv",
        "inventory_dispositions.csv", "state_transition_log.csv",
        "ground_truth.csv", "company_financials.csv", "manifest.json"
    ]
    for ef in expected_files:
        assert os.path.exists(os.path.join(test_dir, ef)), f"Missing {ef}"

    # Validate integrity
    summary = validate_all(data_dir=test_dir)
    assert summary["status"] == "PASSED"

    # Clean up test dir
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)


def test_baseline_dataset_integrity():
    data_dir = "data"
    assert os.path.exists(os.path.join(data_dir, "orders.csv")), "Baseline data not found"

    summary = validate_all(data_dir=data_dir)
    assert summary["status"] == "PASSED"
    assert summary["checks"]["fk_integrity"]["status"] == "PASSED"
    assert summary["checks"]["refund_math_reconciliation"]["is_valid"] is True


def test_ground_truth_edge_cases():
    data_dir = "data"
    gt_path = os.path.join(data_dir, "ground_truth.csv")
    assert os.path.exists(gt_path)

    df = pd.read_csv(gt_path)
    anomaly_types = set(df["anomaly_type"])

    # Required edge cases per problem statement:
    # 1. Return quantity exceeds purchased quantity
    # 2. Refund exceeds paid amount
    # 3. Restock before inspection
    # 4. Return after policy window without override
    # 5. Duplicate refund
    assert "return_qty_exceeds_purchased" in anomaly_types
    assert "refund_exceeds_paid" in anomaly_types
    assert "restock_before_inspection" in anomaly_types
    assert "late_return_no_override" in anomaly_types
    assert "duplicate_refund" in anomaly_types
