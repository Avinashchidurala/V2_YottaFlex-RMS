"""
Reproducibility Test Script
Generates data twice with fixed seed 20261022 into separate directories (test_run1, test_run2)
and checks that every single file has the exact same row count and SHA256 checksum.
"""

import os
import shutil
import hashlib
from data_generator.generator import RMSDataGenerator


def test_reproducibility():
    dir1 = "data_test_run1"
    dir2 = "data_test_run2"

    print("[*] Running Pass 1 (seed=20261022, scale=0.05)...")
    gen1 = RMSDataGenerator(seed=20261022, scale=0.05, output_dir=dir1)
    gen1.generate_all()

    print("\n[*] Running Pass 2 (seed=20261022, scale=0.05)...")
    gen2 = RMSDataGenerator(seed=20261022, scale=0.05, output_dir=dir2)
    gen2.generate_all()

    print("\n[*] Comparing Checksums between Pass 1 and Pass 2...")
    all_match = True
    for fname in sorted(os.listdir(dir1)):
        p1 = os.path.join(dir1, fname)
        p2 = os.path.join(dir2, fname)
        with open(p1, "rb") as f1, open(p2, "rb") as f2:
            h1 = hashlib.sha256(f1.read()).hexdigest()
            h2 = hashlib.sha256(f2.read()).hexdigest()
        match = (h1 == h2)
        print(f"    - {fname:30s}: {'MATCH ✓' if match else 'MISMATCH ✗'} ({h1[:12]} vs {h2[:12]})")
        if not match:
            all_match = False

    # Cleanup test dirs
    shutil.rmtree(dir1, ignore_errors=True)
    shutil.rmtree(dir2, ignore_errors=True)

    if all_match:
        print("\n[✓] 100% REPRODUCIBILITY VERIFIED! Both passes match perfectly.")
    else:
        print("\n[✗] Reproducibility test failed.")
        exit(1)


if __name__ == "__main__":
    test_reproducibility()
