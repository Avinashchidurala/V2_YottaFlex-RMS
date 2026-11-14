"""
Configuration and constants for the Returns Management System (RMS) Data Generator.
Currency: INR (Indian Rupee - ₹)
Deterministic seed: 20261022
"""

SEED = 20261022

# Strict volume targets per problem specification
BASELINE_ORDERS = 30000
BASELINE_RETURN_REQUESTS = 5000
BASELINE_RETURN_LINES = 8000

# Exactly 3 Customers for the Customer Panels and all purchase orders
CORE_CUSTOMERS = [
    {
        "customer_id": "CUST-IND-001",
        "name": "John Smith",
        "email": "john.smith@example.in",
        "phone": "+91-9876543210",
        "address": "42, MG Road, Indiranagar",
        "city": "Bangalore",
        "state": "Karnataka",
        "tier": "vip",
        "initial_wallet_inr": 25000.0,
    },
    {
        "customer_id": "CUST-IND-002",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@example.in",
        "phone": "+91-9823456789",
        "address": "15, Linking Road, Bandra West",
        "city": "Mumbai",
        "state": "Maharashtra",
        "tier": "premium",
        "initial_wallet_inr": 18500.0,
    },
    {
        "customer_id": "CUST-IND-003",
        "name": "Michael Brown",
        "email": "michael.brown@example.in",
        "phone": "+91-9811223344",
        "address": "88, Connaught Place",
        "city": "Delhi",
        "state": "Delhi",
        "tier": "standard",
        "initial_wallet_inr": 12000.0,
    }
]

# Product Catalog with Initial Stock, Pricing (INR), Category, Return Windows
PRODUCTS_CATALOG = [
    {"product_id": "PROD-ELEC-001", "name": "Samsung Galaxy S24 Ultra", "category": "electronics", "unit_price_inr": 129999.0, "cost_price_inr": 98000.0, "stock": 500, "return_window_days": 7, "is_returnable": True, "gst_pct": 18.0},
    {"product_id": "PROD-ELEC-002", "name": "boAt Nirvana ANC Headphones", "category": "electronics", "unit_price_inr": 3999.0, "cost_price_inr": 2100.0, "stock": 1500, "return_window_days": 7, "is_returnable": True, "gst_pct": 18.0},
    {"product_id": "PROD-ELEC-003", "name": "Apple MacBook Air M3", "category": "electronics", "unit_price_inr": 114900.0, "cost_price_inr": 89000.0, "stock": 300, "return_window_days": 7, "is_returnable": True, "gst_pct": 18.0},
    {"product_id": "PROD-CLOTH-001", "name": "Fabindia Men Khadi Cotton Kurta", "category": "clothing", "unit_price_inr": 2490.0, "cost_price_inr": 1100.0, "stock": 1200, "return_window_days": 7, "is_returnable": True, "gst_pct": 12.0},
    {"product_id": "PROD-CLOTH-002", "name": "Biba Women Anarkali Suit Set", "category": "clothing", "unit_price_inr": 4999.0, "cost_price_inr": 2200.0, "stock": 900, "return_window_days": 7, "is_returnable": True, "gst_pct": 12.0},
    {"product_id": "PROD-BOOK-001", "name": "The Psychology of Money (Paperback)", "category": "books", "unit_price_inr": 399.0, "cost_price_inr": 180.0, "stock": 2000, "return_window_days": 7, "is_returnable": True, "gst_pct": 5.0},
    {"product_id": "PROD-APPL-001", "name": "Prestige Deluxe Alpha Pressure Cooker 5L", "category": "home_appliances", "unit_price_inr": 2850.0, "cost_price_inr": 1600.0, "stock": 1000, "return_window_days": 7, "is_returnable": True, "gst_pct": 18.0},
    {"product_id": "PROD-APPL-002", "name": "Philips Digital Air Fryer HD9252", "category": "home_appliances", "unit_price_inr": 7999.0, "cost_price_inr": 5100.0, "stock": 600, "return_window_days": 7, "is_returnable": True, "gst_pct": 18.0},
    {"product_id": "PROD-FURN-001", "name": "Wakefit Ergonomic Office Chair", "category": "furniture", "unit_price_inr": 8499.0, "cost_price_inr": 4800.0, "stock": 400, "return_window_days": 7, "is_returnable": True, "gst_pct": 18.0},
    {"product_id": "PROD-JEWL-001", "name": "Tanishq 22K Gold Stud Earrings", "category": "jewelry", "unit_price_inr": 34500.0, "cost_price_inr": 29000.0, "stock": 200, "return_window_days": 7, "is_returnable": True, "gst_pct": 3.0},
    {"product_id": "PROD-SPRT-001", "name": "Nivia Storm Football (Size 5)", "category": "sports", "unit_price_inr": 899.0, "cost_price_inr": 420.0, "stock": 1500, "return_window_days": 7, "is_returnable": True, "gst_pct": 12.0},
    {"product_id": "PROD-TOYS-001", "name": "LEGO Classic Medium Creative Brick Box", "category": "toys", "unit_price_inr": 2999.0, "cost_price_inr": 1650.0, "stock": 700, "return_window_days": 7, "is_returnable": True, "gst_pct": 12.0},
    {"product_id": "PROD-PERISH-001", "name": "Alphonso Mango Box 1 Dozen", "category": "perishables", "unit_price_inr": 1200.0, "cost_price_inr": 700.0, "stock": 350, "return_window_days": 0, "is_returnable": False, "gst_pct": 0.0},
    {"product_id": "PROD-BEAUTY-001", "name": "Forest Essentials Soundarya Radiance Cream", "category": "beauty", "unit_price_inr": 3800.0, "cost_price_inr": 1900.0, "stock": 800, "return_window_days": 0, "is_returnable": False, "gst_pct": 18.0},
]

RETURN_REASONS = [
    "defective",
    "wrong_item",
    "not_as_described",
    "changed_mind",
    "damaged_in_transit",
    "sizing_issue",
    "quality_issue"
]

PAYMENT_METHODS = ["upi", "credit_card", "debit_card", "net_banking", "cod", "emi"]
ORDER_STATUSES = ["delivered", "shipping", "confirmed", "pending", "cancelled"]
DISPOSITION_ACTIONS = ["restock", "refurbish", "quarantine", "scrap"]
INSPECTION_CONDITIONS = ["excellent", "good", "fair", "poor", "unusable"]

# Anomaly counts injected
ANOMALY_TARGETS = {
    "return_qty_exceeds_purchased": 50,
    "refund_exceeds_paid": 30,
    "restock_before_inspection": 25,
    "late_return_no_override": 40,
    "duplicate_refund": 35,
    "missing_shipment": 20,
}
