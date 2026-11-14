# Source Manifest & Data Provenance — Returns Management System (RMS)

## Generation Metadata
- **Deterministic Random Seed**: `20261022`
- **Currency**: `INR` (Indian Rupee - ₹)
- **Scale Factor**: `1.0` (Full challenge volume)
- **Generator Script**: `data_generator/generator.py` (CLI: `run_generator.py`)
- **Validation Script**: `data_generator/validator.py`
- **Output Directory**: `./data/`
- **Target Baseline Orders**: 30,000
- **Target Return Requests**: 5,000
- **Target Return Lines**: 8,000
- **Core Customers for Panels**: 3
- **Labelled Ground Truth Anomalies**: 200

---

## Datasets Manifest & Integrity Checksums

All datasets generated with seed `20261022` are strictly reproducible. SHA256 hashes:

| Dataset File | Row Count | Columns Count | SHA256 Checksum |
|---|---|---|---|
| `customers.csv` | 3 | 11 | `bffee004ba15ca35dc76e9fdbb004e5fa216f4ea5862b642dda7a2855c03e76e` |
| `inventory.csv` | 14 | 11 | `b7d1831c96e02a775e96fa0f66e25a53a305273079d9ee5018505a3f20ed26ac` |
| `orders.csv` | 30,000 | 10 | `67da7a1ba4d7cfb3115f633422bccdbee15445de9243ba38f674852d6b11696e` |
| `order_lines.csv` | 54,163 | 12 | `9c26aa28b88fdc455dc1e0e7e52b181e9cdfa7d57f3787d8856e6c14adf04c08` |
| `return_requests.csv` | 5,000 | 11 | `ea9f8c2755c7ff442d997289a3460eba54bba0cdd8e2e5a4aa64c322dd7b9ffb` |
| `return_lines.csv` | 8,000 | 7 | `aaebb7700112d2ac44ea398eb9f0458b68958fd59b22ae5a258e04806987fff6` |
| `return_authorizations.csv` | 3,352 | 6 | `5cf366be81bc3fe13c1f5f5a9eea50555fbcb748f8994b04ea0d3eca38f27c40` |
| `return_shipments.csv` | 3,352 | 8 | `6ef712ec37e173ade0c81d98e3de9c5b9e375e3e4b1f9686419ff29737d95918` |
| `inspections.csv` | 3,332 | 7 | `89a60df0249cdd985f55a2eb2bc1d7706794657dea25165e9062635ad449ebea` |
| `refunds.csv` | 4,117 | 12 | `bc796baa0b94101d61214b6aeb3d6e5ced328430ac677a5f1dfeaf3c699c9103` |
| `inventory_dispositions.csv` | 4,082 | 10 | `52978928a9e0bf2d68edfb38c684a7b4db994aa2fd41d2984a2522f5dc8ccd25` |
| `state_transition_log.csv` | 750 | 8 | `b5216a1298b7313bd144e90bbe401bc747fc60d904fa4a52c4c0276a5b3cadcd` |
| `ground_truth.csv` | 200 | 8 | `0989343d921e9fcb901e9b123ffba66c9ccbe9c9268ac428741a51ab5c9f2c72` |

---

## Lawful Provenance & Public Data Guidance

1. **Synthetic Nature**: 100% of rows are generated algorithmically using mathematical distributions, domain constraints, and deterministic pseudorandom number generators in Python.
2. **No Scraping / Protected Data**: No external websites were scraped. No personally identifiable information (PII) from private or proprietary databases was harvested.
3. **Reference Attribution**:
   - Product catalog schema inspired by standard Indian e-commerce category classifications (Electronics, Apparel, Home Appliances, Books).
   - Names and geographical distributions generated from standard demographic frequency tables (Ministry of Statistics and Programme Implementation - India, open public data).
4. **Reproducibility Guarantee**:
   Run `python test_reproducibility.py` to regenerate in two isolated passes and prove exact bitwise equivalence.
